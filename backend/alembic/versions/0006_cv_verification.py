"""0006_cv_verification

Revision ID: 0006_cv_verification
Revises: 0005_career_and_study_catalog
Create Date: 2026-09-25

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0006_cv_verification'
down_revision: Union[str, None] = '0005_career_and_study_catalog'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'verification_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('school_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('cv_snapshot_id', sa.String(length=64), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('display_code', sa.String(length=32), nullable=False),
        sa.Column('snapshot_digest', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('revocation_reason', sa.Text(), nullable=True),
        sa.Column('pdf_storage_object_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['revoked_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['pdf_storage_object_id'], ['storage_objects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('ix_verification_records_school_id', 'verification_records', ['school_id'])
    op.create_index('ix_verification_records_student_id', 'verification_records', ['student_id'])
    op.create_index('ix_verification_records_cv_snapshot_id', 'verification_records', ['cv_snapshot_id'])
    op.create_index('ix_verification_records_token_hash', 'verification_records', ['token_hash'], unique=True)
    op.create_index('ix_verification_records_display_code', 'verification_records', ['display_code'], unique=True)
    op.create_index(
        'ix_verification_records_school_student_issued',
        'verification_records',
        ['school_id', 'student_id', 'issued_at'],
    )
    op.create_index(
        'ix_verification_records_status_expires',
        'verification_records',
        ['status', 'expires_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_verification_records_status_expires', table_name='verification_records')
    op.drop_index('ix_verification_records_school_student_issued', table_name='verification_records')
    op.drop_index('ix_verification_records_display_code', table_name='verification_records')
    op.drop_index('ix_verification_records_token_hash', table_name='verification_records')
    op.drop_index('ix_verification_records_cv_snapshot_id', table_name='verification_records')
    op.drop_index('ix_verification_records_student_id', table_name='verification_records')
    op.drop_index('ix_verification_records_school_id', table_name='verification_records')
    op.drop_table('verification_records')
