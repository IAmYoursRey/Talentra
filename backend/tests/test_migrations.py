import os
import pytest
from alembic.config import Config
from alembic import command
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.database import Base


def test_alembic_migrations_lifecycle(tmp_path):
    """
    MANDATORY REQUIREMENT 49:
    1. Clean database -> alembic upgrade head -> verify all expected tables exist.
    2. Downgrade one revision -> verify downgrade succeeds.
    3. Upgrade head again -> verify upgrade succeeds.
    """
    db_file = tmp_path / "migration_test.db"
    sync_db_url = f"sqlite:///{db_file.as_posix()}"
    async_db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    alembic_ini_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("sqlalchemy.url", async_db_url)

    # 1. Run upgrade head
    command.upgrade(alembic_cfg, "head")

    # Verify tables created
    from sqlalchemy import create_engine
    sync_engine = create_engine(sync_db_url)
    inspector = inspect(sync_engine)
    tables = inspector.get_table_names()

    expected_tables = {
        "schools",
        "users",
        "auth_identities",
        "student_profiles",
        "teacher_profiles",
        "classes",
        "enrollments",
        "teacher_assignments",
        "sessions",
        "audit_events",
        "storage_objects",
        "password_reset_tokens",
        "idempotency_keys",
        "outbox_events",
        "skill_tags",
        "validation_decisions",
        "rubric_assessments",
        "career_paths",
        "study_paths",
        "verification_records",
        "alembic_version",
    }

    for table in expected_tables:
        assert table in tables, f"Expected table '{table}' missing from migrated schema!"

    sync_engine.dispose()

    # 2. Downgrade to base
    command.downgrade(alembic_cfg, "base")

    sync_engine2 = create_engine(sync_db_url)
    inspector2 = inspect(sync_engine2)
    tables_after_downgrade = inspector2.get_table_names()
    assert "users" not in tables_after_downgrade
    assert "schools" not in tables_after_downgrade
    sync_engine2.dispose()

    # 3. Upgrade back to head
    command.upgrade(alembic_cfg, "head")

    sync_engine3 = create_engine(sync_db_url)
    inspector3 = inspect(sync_engine3)
    tables_after_reupgrade = inspector3.get_table_names()
    for table in expected_tables:
        assert table in tables_after_reupgrade, f"Expected table '{table}' missing after re-upgrade!"
    sync_engine3.dispose()
