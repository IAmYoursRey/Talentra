"""0002_portfolio_tag_catalog

Revision ID: 0002_portfolio_tag_catalog
Revises: 0001_core_relational
Create Date: 2026-09-25

"""
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0002_portfolio_tag_catalog'
down_revision: Union[str, None] = '0001_core_relational'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INITIAL_TAGS = [
    ("web-development", "Web Development", "technical", "Pengembangan aplikasi web frontend & backend modern", 1),
    ("ui-ux", "UI/UX Design", "creative", "Desain antarmuka, pengalaman pengguna, dan wireframing", 2),
    ("problem-solving", "Problem Solving", "problem_solving", "Kemampuan pemecahan masalah algoritma dan teknis", 3),
    ("leadership", "Leadership", "leadership", "Kepemimpinan tim, koordinasi proyek, dan delegasi", 4),
    ("teamwork", "Teamwork & Kolaborasi", "collaboration", "Kerja sama lintas disiplin dalam menyelesaikan proyek", 5),
    ("public-speaking", "Public Speaking", "communication", "Presentasi publik, pitch ide, dan komunikasi verbal", 6),
    ("event-management", "Event Management", "leadership", "Perencanaan, pelaksanaan, dan manajemen acara sekolah/komunitas", 7),
    ("data-analysis", "Data Analysis", "technical", "Pengolahan, analisis data, dan visualisasi statistik", 8),
    ("graphic-design", "Graphic Design", "creative", "Desain grafis, branding visual, dan ilustrasi digital", 9),
    ("research", "Research & Riset", "problem_solving", "Riset ilmiah, investigasi literatur, dan metodologi eksperimen", 10),
    ("writing", "Technical Writing", "communication", "Penulisan teknis, dokumentasi sistem, dan penyusunan laporan", 11),
    ("video-editing", "Video Editing", "creative", "Penyuntingan video multimedia, sinematografi, dan animasi visual", 12),
    ("creativity", "Kreativitas & Inovasi", "creative", "Penciptaan solusi orisinal dan inovasi produk baru", 13),
    ("digital-literacy", "Digital Literacy", "technical", "Literasi perangkat digital, etika siber, dan kolaborasi cloud", 14),
]


def upgrade() -> None:
    skill_tags_table = op.create_table(
        'skill_tags',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('display_name', sa.String(length=128), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_skill_tags_code', 'skill_tags', ['code'], unique=True)

    now = datetime.now(timezone.utc)
    tag_rows = [
        {
            "id": f"tag_{code.replace('-', '_')}",
            "code": code,
            "display_name": name,
            "category": category,
            "description": desc,
            "active": True,
            "sort_order": order,
            "created_at": now,
            "updated_at": now,
        }
        for code, name, category, desc, order in INITIAL_TAGS
    ]
    op.bulk_insert(skill_tags_table, tag_rows)


def downgrade() -> None:
    op.drop_index('ix_skill_tags_code', table_name='skill_tags')
    op.drop_table('skill_tags')
