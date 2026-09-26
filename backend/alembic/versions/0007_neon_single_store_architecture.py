"""0007_neon_single_store_architecture

Revision ID: 0007_neon_single_store_architecture
Revises: 0006_cv_verification
Create Date: 2026-09-26

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0007_neon_single_store_architecture'
down_revision: Union[str, None] = '0006_cv_verification'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

portable_json = sa.JSON().with_variant(postgresql.JSONB(), 'postgresql')


def upgrade() -> None:
    # 1. portfolio_items
    op.create_table(
        'portfolio_items',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('school_id', sa.String(length=36), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('activity_type', sa.String(length=64), nullable=False),
        sa.Column('activity_date', sa.String(length=32), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('canonical_tag_ids', portable_json, nullable=False),
        sa.Column('evidence_refs', portable_json, nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('current_revision_id', sa.String(length=36), nullable=False),
        sa.Column('current_revision', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('current_revision_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('teacher_feedback', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_portfolio_items_school_id', 'portfolio_items', ['school_id'])
    op.create_index('ix_portfolio_items_student_id', 'portfolio_items', ['student_id'])
    op.create_index('ix_portfolio_items_status', 'portfolio_items', ['status'])
    op.create_index('ix_portfolio_items_school_student_status', 'portfolio_items', ['school_id', 'student_id', 'status'])
    op.create_index('ix_portfolio_items_school_status_created', 'portfolio_items', ['school_id', 'status', 'created_at'])

    # 2. portfolio_revisions
    op.create_table(
        'portfolio_revisions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('portfolio_id', sa.String(length=36), sa.ForeignKey('portfolio_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('title_snapshot', sa.String(length=255), nullable=False),
        sa.Column('activity_type_snapshot', sa.String(length=64), nullable=False),
        sa.Column('description_snapshot', sa.Text(), nullable=False),
        sa.Column('tag_snapshot', portable_json, nullable=False),
        sa.Column('evidence_refs', portable_json, nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_portfolio_revisions_portfolio_id', 'portfolio_revisions', ['portfolio_id'])
    op.create_index('ix_portfolio_revisions_school_id', 'portfolio_revisions', ['school_id'])
    op.create_index('ix_portfolio_revisions_student_id', 'portfolio_revisions', ['student_id'])
    op.create_index('ix_portfolio_revisions_portfolio_version', 'portfolio_revisions', ['portfolio_id', 'version'])

    # 3. evidence_tag_snapshots
    op.create_table(
        'evidence_tag_snapshots',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('school_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('portfolio_id', sa.String(length=36), nullable=False),
        sa.Column('revision_id', sa.String(length=36), nullable=False),
        sa.Column('validation_decision_id', sa.String(length=36), nullable=False, unique=True),
        sa.Column('canonical_tag_ids', portable_json, nullable=False),
        sa.Column('canonical_tag_codes', portable_json, nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('projection_version', sa.String(length=32), nullable=False, server_default='v1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_evidence_tag_snapshots_school_id', 'evidence_tag_snapshots', ['school_id'])
    op.create_index('ix_evidence_tag_snapshots_student_id', 'evidence_tag_snapshots', ['student_id'])
    op.create_index('ix_evidence_tag_snapshots_portfolio_id', 'evidence_tag_snapshots', ['portfolio_id'])
    op.create_index('ix_evidence_tag_snapshots_validation_decision_id', 'evidence_tag_snapshots', ['validation_decision_id'])
    op.create_index('ix_evidence_tag_snapshots_student_approved', 'evidence_tag_snapshots', ['student_id', 'approved_at'])
    op.create_index('ix_evidence_tag_snapshots_school_student', 'evidence_tag_snapshots', ['school_id', 'student_id'])

    # 4. recommendation_snapshots
    op.create_table(
        'recommendation_snapshots',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('school_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('source_fingerprint', sa.String(length=64), nullable=False),
        sa.Column('catalog_version', sa.String(length=64), nullable=False, server_default='career-catalog-v1'),
        sa.Column('scoring_version', sa.String(length=64), nullable=False, server_default='recommendation-v1'),
        sa.Column('mapping_version', sa.String(length=64), nullable=False, server_default='mapping-v1'),
        sa.Column('evidence_confidence', portable_json, nullable=False),
        sa.Column('career_results', portable_json, nullable=False),
        sa.Column('study_results', portable_json, nullable=False),
        sa.Column('supporting_approval_ids', portable_json, nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_recommendation_snapshots_school_id', 'recommendation_snapshots', ['school_id'])
    op.create_index('ix_recommendation_snapshots_student_id', 'recommendation_snapshots', ['student_id'])
    op.create_index('ix_recommendation_snapshots_student_generated', 'recommendation_snapshots', ['student_id', 'generated_at'])

    # 5. derived_professional_descriptions
    op.create_table(
        'derived_professional_descriptions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('school_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('portfolio_id', sa.String(length=36), nullable=False),
        sa.Column('revision_id', sa.String(length=36), nullable=False),
        sa.Column('source_hash', sa.String(length=64), nullable=False),
        sa.Column('original_title', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('professional_text', sa.Text(), nullable=False, server_default=''),
        sa.Column('translator_version', sa.String(length=64), nullable=False, server_default='industry-language-v1'),
        sa.Column('mode', sa.String(length=32), nullable=False, server_default='deterministic'),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_derived_descriptions_school_id', 'derived_professional_descriptions', ['school_id'])
    op.create_index('ix_derived_descriptions_student_id', 'derived_professional_descriptions', ['student_id'])
    op.create_index('ix_derived_descriptions_portfolio_id', 'derived_professional_descriptions', ['portfolio_id'])
    op.create_index('ix_derived_descriptions_portfolio_revision', 'derived_professional_descriptions', ['portfolio_id', 'revision_id'])
    op.create_index('ix_derived_descriptions_student_portfolio', 'derived_professional_descriptions', ['student_id', 'portfolio_id'])

    # 6. cv_content_snapshots
    op.create_table(
        'cv_content_snapshots',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('school_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('snapshot_version', sa.String(length=32), nullable=False, server_default='cv-snapshot-v1'),
        sa.Column('renderer_version', sa.String(length=32), nullable=False, server_default='cv-pdf-v1'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='issued'),
        sa.Column('profile', portable_json, nullable=False),
        sa.Column('approved_skills', portable_json, nullable=False),
        sa.Column('teacher_validated_competencies', portable_json, nullable=False),
        sa.Column('selected_portfolios', portable_json, nullable=False),
        sa.Column('optional_exploration_summary', portable_json, nullable=True),
        sa.Column('content_digest', sa.String(length=64), nullable=False),
        sa.Column('pdf_storage_key', sa.String(length=512), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_cv_content_snapshots_school_id', 'cv_content_snapshots', ['school_id'])
    op.create_index('ix_cv_content_snapshots_student_id', 'cv_content_snapshots', ['student_id'])
    op.create_index('ix_cv_content_snapshots_content_digest', 'cv_content_snapshots', ['content_digest'])
    op.create_index('ix_cv_content_snapshots_student_status', 'cv_content_snapshots', ['student_id', 'status'])
    op.create_index('ix_cv_content_snapshots_student_digest', 'cv_content_snapshots', ['student_id', 'content_digest'])

    # 7. blob_upload_intents
    op.create_table(
        'blob_upload_intents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('token_hash', sa.String(length=64), nullable=False, unique=True),
        sa.Column('school_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('portfolio_id', sa.String(length=36), nullable=False),
        sa.Column('pathname', sa.String(length=512), nullable=False),
        sa.Column('expected_content_type', sa.String(length=128), nullable=False),
        sa.Column('max_bytes', sa.BigInteger(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_blob_upload_intents_token_hash', 'blob_upload_intents', ['token_hash'])
    op.create_index('ix_blob_upload_intents_school_id', 'blob_upload_intents', ['school_id'])
    op.create_index('ix_blob_upload_intents_student_id', 'blob_upload_intents', ['student_id'])
    op.create_index('ix_blob_upload_intents_portfolio_id', 'blob_upload_intents', ['portfolio_id'])
    op.create_index('ix_blob_upload_intents_portfolio_status', 'blob_upload_intents', ['portfolio_id', 'status'])

    # 8. rate_limit_buckets
    op.create_table(
        'rate_limit_buckets',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('scope', sa.String(length=32), nullable=False),
        sa.Column('window_start', sa.BigInteger(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('key_hash', 'scope', 'window_start', name='uq_rate_limit_bucket'),
    )
    op.create_index('ix_rate_limit_buckets_key_hash', 'rate_limit_buckets', ['key_hash'])
    op.create_index('ix_rate_limit_buckets_scope', 'rate_limit_buckets', ['scope'])
    op.create_index('ix_rate_limit_buckets_expires_at', 'rate_limit_buckets', ['expires_at'])


def downgrade() -> None:
    op.drop_table('rate_limit_buckets')
    op.drop_table('blob_upload_intents')
    op.drop_table('cv_content_snapshots')
    op.drop_table('derived_professional_descriptions')
    op.drop_table('recommendation_snapshots')
    op.drop_table('evidence_tag_snapshots')
    op.drop_table('portfolio_revisions')
    op.drop_table('portfolio_items')
