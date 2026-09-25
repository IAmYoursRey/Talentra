---
name: talentra-auth-rbac
description: Implement TALENTRA authentication, JWT/session behavior, post-login role routing, and server-enforced RBAC for student, teacher, and admin roles.
---

# Auth/RBAC procedure

1. Read `TALENTRA/references/security-privacy.md`.
2. Inspect current auth framework before adding dependencies.
3. Define canonical `student | teacher | admin` role in the relational model.
4. Normalize login identities behind an auth-identity layer; do not make NISN/NIP/NUPTK/NPSN the internal primary key.
5. Choose and document JWT/access-refresh storage/rotation behavior.
6. Implement server middleware/dependencies for:
   - authenticated identity,
   - school tenant,
   - role,
   - resource ownership / teacher assignment,
   - state-specific permission.
7. Implement canonical role redirect after authentication.
8. Add 401/403 behavior.
9. Add negative authorization tests across roles and tenants.
10. Add password change/recovery without exposing existing passwords.

Never accept a role supplied by the browser as authority.
