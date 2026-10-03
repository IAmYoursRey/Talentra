"""0003_teacher_validation_and_rubrics

Revision ID: 0003_teacher_val_rubrics
Revises: 0002_portfolio_tag_catalog
Create Date: 2026-09-25

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0003_teacher_val_rubrics'
down_revision: Union[str, None] = '0002_portfolio_tag_catalog'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TAG_RADAR_MAPPINGS = {
    "public-speaking": "communication",
    "writing": "communication",
    "leadership": "leadership",
    "event-management": "leadership",
    "web-development": "digital-literacy",
    "data-analysis": "digital-literacy",
    "video-editing": "digital-literacy",
    "digital-literacy": "digital-literacy",
    "problem-solving": "problem-solving",
    "research": "problem-solving",
    "ui-ux": "creativity",
    "graphic-design": "creativity",
    "creativity": "creativity",
    "teamwork": "collaboration",
}


def upgrade() -> None:
    op.add_column(
        'skill_tags',
        sa.Column('radar_dimension', sa.String(length=64), nullable=False, server_default='creativity')
    )

    bind = op.get_bind()
    for code, dimension in TAG_RADAR_MAPPINGS.items():
        bind.execute(
            sa.text("UPDATE skill_tags SET radar_dimension = :dimension WHERE code = :code"),
            {"dimension": dimension, "code": code}
        )

    op.create_table(
        'validation_decisions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('portfolio_id', sa.String(length=36), nullable=False),
        sa.Column('revision_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_assignment_id', sa.String(length=36), sa.ForeignKey('teacher_assignments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(length=32), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('application_status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_code', sa.String(length=64), nullable=True),
        sa.Column('idempotency_key_hash', sa.String(length=64), nullable=True),
    )
    op.create_index('ix_validation_decisions_school_id', 'validation_decisions', ['school_id'])
    op.create_index('ix_validation_decisions_portfolio_id', 'validation_decisions', ['portfolio_id'])
    op.create_index('ix_validation_decisions_revision_id', 'validation_decisions', ['revision_id'])
    op.create_index('ix_validation_decisions_student_id', 'validation_decisions', ['student_id'])
    op.create_index('ix_validation_decisions_teacher_id', 'validation_decisions', ['teacher_id'])
    op.create_index('ix_validation_decisions_idempotency_key_hash', 'validation_decisions', ['idempotency_key_hash'])
    op.create_index('ix_val_dec_rev_status', 'validation_decisions', ['revision_id', 'application_status'])

    op.create_table(
        'rubric_assessments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('decision_id', sa.String(length=36), sa.ForeignKey('validation_decisions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('portfolio_id', sa.String(length=36), nullable=False),
        sa.Column('revision_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dimension_code', sa.String(length=64), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('decision_id', 'dimension_code', name='uq_decision_dimension'),
        sa.CheckConstraint('score >= 1 AND score <= 5', name='ck_rubric_score_range'),
    )
    op.create_index('ix_rubric_assessments_school_id', 'rubric_assessments', ['school_id'])
    op.create_index('ix_rubric_assessments_decision_id', 'rubric_assessments', ['decision_id'])
    op.create_index('ix_rubric_assessments_portfolio_id', 'rubric_assessments', ['portfolio_id'])
    op.create_index('ix_rubric_assessments_revision_id', 'rubric_assessments', ['revision_id'])
    op.create_index('ix_rubric_assessments_student_id', 'rubric_assessments', ['student_id'])
    op.create_index('ix_rubric_assessments_teacher_id', 'rubric_assessments', ['teacher_id'])


def downgrade() -> None:
    op.drop_table('rubric_assessments')
    op.drop_table('validation_decisions')
    op.drop_column('skill_tags', 'radar_dimension')
