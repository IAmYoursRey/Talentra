"""
TALENTRA.ID Initial School & Admin Bootstrap CLI
Secure operator utility to bootstrap a new school tenant and primary administrator.

Usage:
    python -m app.scripts.bootstrap_school_admin --school-name "SMK Negeri 1 Jakarta" --admin-name "Administrator" --admin-identifier "admin@smkn1jakarta.sch.id" [--identifier-type email]
"""

import argparse
import asyncio
import os
import secrets
import sys
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password, compute_identifier_lookup_hash
from app.domain.normalizers import normalize_login_identifier
from app.db.models import SchoolModel, UserModel, AuthIdentityModel, AuditEventModel


async def bootstrap_school_admin(
    school_name: str,
    admin_name: str,
    admin_identifier: str,
    identifier_type: str = "email",
    school_id: str | None = None,
) -> dict:
    """
    Bootstraps a school and its primary administrator account.
    Enforces server-generated temporary password, must_change_password=True,
    and Argon2id cryptographic hashing.
    """
    norm_res = normalize_login_identifier(admin_identifier)
    normalized_type = norm_res.identifier_type.value
    normalized_val = norm_res.normalized
    lookup_hash = compute_identifier_lookup_hash(normalized_val)
    last4 = normalized_val[-4:] if len(normalized_val) >= 4 else normalized_val

    # Generate high-entropy temporary password
    temp_password = secrets.token_urlsafe(16)
    password_hash = hash_password(temp_password)

    actual_school_id = school_id or f"sch_{uuid.uuid4().hex[:12]}"
    user_id = f"usr_adm_{uuid.uuid4().hex[:12]}"

    async with AsyncSessionLocal() as session:
        # Check if identity already exists
        stmt_check = select(AuthIdentityModel.id).where(
            AuthIdentityModel.identifier_type == normalized_type,
            AuthIdentityModel.identifier_lookup_hash == lookup_hash,
        )
        existing = (await session.execute(stmt_check)).scalar_one_or_none()
        if existing:
            raise ValueError(f"An account with identifier [{identifier_type}] already exists.")

        # Create School
        school = SchoolModel(
            id=actual_school_id,
            name=school_name.strip(),
            status="active",
        )
        session.add(school)

        # Create Admin User
        user = UserModel(
            id=user_id,
            school_id=actual_school_id,
            role="admin",
            status="active",
            display_name=admin_name.strip(),
            email=normalized_val if normalized_type == "email" else None,
        )
        session.add(user)

        # Create Auth Identity with forced password change
        identity = AuthIdentityModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            identifier_type=normalized_type,
            identifier_lookup_hash=lookup_hash,
            identifier_last4=last4,
            password_hash=password_hash,
            active=True,
            must_change_password=True,
        )
        session.add(identity)

        import json
        # Audit Event (No plaintext password logged)
        audit_event = AuditEventModel(
            id=str(uuid.uuid4()),
            school_id=actual_school_id,
            actor_user_id=user_id,
            event_type="BOOTSTRAP_SCHOOL_ADMIN",
            resource_type="school",
            resource_id=actual_school_id,
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            metadata_json=json.dumps({
                "school_name": school_name,
                "admin_name": admin_name,
                "identifier_type": normalized_type,
                "identifier_last4": last4,
            }),
        )
        session.add(audit_event)

        await session.commit()

    return {
        "school_id": actual_school_id,
        "school_name": school_name,
        "admin_user_id": user_id,
        "admin_identifier": normalized_val,
        "identifier_type": normalized_type,
        "temporary_password": temp_password,
        "must_change_password": True,
    }


def main():
    parser = argparse.ArgumentParser(description="Bootstrap TALENTRA.ID School and Primary Administrator")
    parser.add_argument("--school-name", required=True, help="Official name of the school / educational institution")
    parser.add_argument("--admin-name", required=True, help="Full display name of the primary administrator")
    parser.add_argument("--admin-identifier", required=True, help="Primary login identifier (email, NIP, or NPSN)")
    parser.add_argument("--identifier-type", default="email", choices=["email", "nip", "npsn", "nuptk"], help="Type of login identifier")
    parser.add_argument("--school-id", required=False, help="Custom school UUID/ID (optional)")

    args = parser.parse_args()

    try:
        result = asyncio.run(
            bootstrap_school_admin(
                school_name=args.school_name,
                admin_name=args.admin_name,
                admin_identifier=args.admin_identifier,
                identifier_type=args.identifier_type,
                school_id=args.school_id,
            )
        )
        print("\n" + "=" * 60)
        print("TALENTRA.ID SCHOOL & ADMIN BOOTSTRAP SUCCESSFUL")
        print("=" * 60)
        print(f"School ID:            {result['school_id']}")
        print(f"School Name:          {result['school_name']}")
        print(f"Admin User ID:        {result['admin_user_id']}")
        print(f"Admin Identifier:     {result['admin_identifier']} ({result['identifier_type']})")
        print(f"Temporary Password:   {result['temporary_password']}")
        print(f"Must Change Password: {result['must_change_password']}")
        print("-" * 60)
        print("IMPORTANT: Securely hand over the temporary password to the school")
        print("administrator. They will be forced to change it on initial login.")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"\nERROR: Failed to bootstrap school admin: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
