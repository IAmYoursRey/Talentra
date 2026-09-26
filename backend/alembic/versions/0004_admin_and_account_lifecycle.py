"""0004_admin_and_account_lifecycle

Revision ID: 0004_admin_and_account_lifecycle
Revises: 0003_teacher_val_rubrics
Create Date: 2026-09-25

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_admin_and_account_lifecycle'
down_revision: Union[str, None] = '0003_teacher_val_rubrics'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add must_change_password column to auth_identities
    op.add_column(
        'auth_identities',
        sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default=sa.false())
    )

    # 2. Add performance & tenant isolation indexes for Phase 6 Admin and Analytics queries
    op.create_index(
        'ix_users_school_role_status',
        'users',
        ['school_id', 'role', 'status'],
    )
    op.create_index(
        'ix_classes_school_year_status',
        'classes',
        ['school_id', 'academic_year', 'status'],
    )
    op.create_index(
        'ix_enrollments_school_class_status',
        'enrollments',
        ['school_id', 'class_id', 'status'],
    )
    op.create_index(
        'ix_enrollments_school_student_year',
        'enrollments',
        ['school_id', 'student_id', 'academic_year'],
    )
    op.create_index(
        'ix_teacher_assignments_school_class_active',
        'teacher_assignments',
        ['school_id', 'class_id', 'active'],
    )
    op.create_index(
        'ix_teacher_assignments_school_teacher_active',
        'teacher_assignments',
        ['school_id', 'teacher_id', 'active'],
    )
    op.create_index(
        'ix_val_dec_school_applied_action',
        'validation_decisions',
        ['school_id', 'applied_at', 'action'],
    )
    op.create_index(
        'ix_rubric_assess_school_student_dim',
        'rubric_assessments',
        ['school_id', 'student_id', 'dimension_code'],
    )


def downgrade() -> None:
    op.drop_index('ix_rubric_assess_school_student_dim', table_name='rubric_assessments')
    op.drop_index('ix_val_dec_school_applied_action', table_name='validation_decisions')
    op.drop_index('ix_teacher_assignments_school_teacher_active', table_name='teacher_assignments')
    op.drop_index('ix_teacher_assignments_school_class_active', table_name='teacher_assignments')
    op.drop_index('ix_enrollments_school_student_year', table_name='enrollments')
    op.drop_index('ix_enrollments_school_class_status', table_name='enrollments')
    op.drop_index('ix_classes_school_year_status', table_name='classes')
    op.drop_index('ix_users_school_role_status', table_name='users')

    with op.batch_alter_table('auth_identities') as batch_op:
        batch_op.drop_column('must_change_password')
