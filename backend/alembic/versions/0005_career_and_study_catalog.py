"""0005_career_and_study_catalog

Revision ID: 0005_career_and_study_catalog
Revises: 0004_admin_and_account_lifecycle
Create Date: 2026-09-25

"""
import json
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005_career_and_study_catalog'
down_revision: Union[str, None] = '0004_admin_and_account_lifecycle'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INITIAL_CAREER_PATHS = [
    {
        "id": "cp_software_dev",
        "code": "software-development",
        "title": "Rekayasa Perangkat Lunak & Aplikasi",
        "cluster": "Teknologi Informasi & Rekayasa Perangkat Lunak",
        "description": "Pengembangan sistem perangkat lunak, arsitektur aplikasi web/mobile, dan rekayasa kode berbasis solusi terstruktur.",
        "radar_weights": json.dumps({
            "digital-literacy": 0.35,
            "problem-solving": 0.35,
            "collaboration": 0.10,
            "creativity": 0.10,
            "communication": 0.05,
            "leadership": 0.05,
        }),
        "tag_weights": json.dumps({
            "web-development": 0.40,
            "problem-solving": 0.30,
            "digital-literacy": 0.15,
            "teamwork": 0.15,
        }),
        "suggested_pathways": json.dumps([
            "Junior Frontend Developer",
            "Junior Backend Developer",
            "Full-Stack Engineer",
            "Software QA Tester",
        ]),
        "sort_order": 1,
    },
    {
        "id": "cp_data_analytics",
        "code": "data-analytics",
        "title": "Sains Data & Analitika Terapan",
        "cluster": "Sains Data & Kecerdasan Komputasi",
        "description": "Eksplorasi pengolahan data, analisis statistik, visualisasi wawasan, dan pemodelan analitik terstruktur.",
        "radar_weights": json.dumps({
            "digital-literacy": 0.30,
            "problem-solving": 0.35,
            "creativity": 0.10,
            "communication": 0.15,
            "collaboration": 0.05,
            "leadership": 0.05,
        }),
        "tag_weights": json.dumps({
            "data-analysis": 0.45,
            "research": 0.25,
            "problem-solving": 0.20,
            "digital-literacy": 0.10,
        }),
        "suggested_pathways": json.dumps([
            "Junior Data Analyst",
            "Business Intelligence Associate",
            "Data Specialist",
            "Research Assistant",
        ]),
        "sort_order": 2,
    },
    {
        "id": "cp_digital_product_uiux",
        "code": "digital-product-uiux",
        "title": "Desain Produk Digital & UI/UX",
        "cluster": "Desain Komunikasi Visual & Media Digital",
        "description": "Perancangan antarmuka visual interaktif, riset pengalaman pengguna, wireframing, dan prototipe aplikasi digital.",
        "radar_weights": json.dumps({
            "creativity": 0.35,
            "digital-literacy": 0.25,
            "communication": 0.15,
            "problem-solving": 0.10,
            "collaboration": 0.10,
            "leadership": 0.05,
        }),
        "tag_weights": json.dumps({
            "ui-ux": 0.45,
            "graphic-design": 0.25,
            "creativity": 0.15,
            "web-development": 0.15,
        }),
        "suggested_pathways": json.dumps([
            "UI/UX Designer",
            "Product Design Associate",
            "Web Designer",
            "Design Researcher",
        ]),
        "sort_order": 3,
    },
    {
        "id": "cp_creative_digital_media",
        "code": "creative-digital-media",
        "title": "Media Kreatif Digital & Konten Visual",
        "cluster": "Seni Media Digital & Animasi",
        "description": "Penciptaan konten multimedia visual, penyuntingan video dinamis, grafis interaktif, dan komunikasi media kreatif.",
        "radar_weights": json.dumps({
            "creativity": 0.40,
            "communication": 0.20,
            "digital-literacy": 0.20,
            "collaboration": 0.10,
            "problem-solving": 0.05,
            "leadership": 0.05,
        }),
        "tag_weights": json.dumps({
            "graphic-design": 0.35,
            "video-editing": 0.35,
            "creativity": 0.20,
            "writing": 0.10,
        }),
        "suggested_pathways": json.dumps([
            "Digital Graphic Designer",
            "Video Editor",
            "Motion Graphic Artist",
            "Creative Media Producer",
        ]),
        "sort_order": 4,
    },
    {
        "id": "cp_cybersecurity_infra",
        "code": "cybersecurity-infrastructure",
        "title": "Keamanan Siber & Infrastruktur Jaringan",
        "cluster": "Jaringan Komputer & Telekomunikasi",
        "description": "Pengelolaan keamanan informasi, konfigurasi infrastruktur jaringan komputasi, dan pemecahan masalah sistem siber.",
        "radar_weights": json.dumps({
            "digital-literacy": 0.35,
            "problem-solving": 0.35,
            "collaboration": 0.10,
            "leadership": 0.10,
            "communication": 0.05,
            "creativity": 0.05,
        }),
        "tag_weights": json.dumps({
            "digital-literacy": 0.40,
            "problem-solving": 0.30,
            "research": 0.20,
            "teamwork": 0.10,
        }),
        "suggested_pathways": json.dumps([
            "Network Administrator",
            "Junior Security Analyst",
            "IT Infrastructure Specialist",
            "Cloud Support Associate",
        ]),
        "sort_order": 5,
    },
    {
        "id": "cp_communication_content",
        "code": "communication-content",
        "title": "Komunikasi Publik & Penulisan Teknis",
        "cluster": "Komunikasi & Manajemen Informasi",
        "description": "Penyampaian gagasan profesional, presentasi publik, penulisan dokumentasi teknis sistem, dan relasi komunikasi.",
        "radar_weights": json.dumps({
            "communication": 0.40,
            "collaboration": 0.20,
            "creativity": 0.15,
            "leadership": 0.15,
            "digital-literacy": 0.05,
            "problem-solving": 0.05,
        }),
        "tag_weights": json.dumps({
            "public-speaking": 0.40,
            "writing": 0.30,
            "teamwork": 0.15,
            "digital-literacy": 0.15,
        }),
        "suggested_pathways": json.dumps([
            "Technical Writer",
            "Public Relations Associate",
            "Content Strategist",
            "Communications Coordinator",
        ]),
        "sort_order": 6,
    },
    {
        "id": "cp_business_entrepreneurship",
        "code": "business-entrepreneurship",
        "title": "Inisiatif Bisnis & Kewirausahaan Digital",
        "cluster": "Bisnis & Manajemen Digital",
        "description": "Inisiasi proyek bernilai tambah, manajemen operasional acara/bisnis, koordinasi tim, dan perancangan strategi pasar.",
        "radar_weights": json.dumps({
            "leadership": 0.35,
            "communication": 0.25,
            "problem-solving": 0.15,
            "collaboration": 0.15,
            "creativity": 0.05,
            "digital-literacy": 0.05,
        }),
        "tag_weights": json.dumps({
            "leadership": 0.40,
            "event-management": 0.30,
            "teamwork": 0.15,
            "public-speaking": 0.15,
        }),
        "suggested_pathways": json.dumps([
            "Digital Entrepreneur",
            "Project Coordinator",
            "Business Development Associate",
            "Operations Specialist",
        ]),
        "sort_order": 7,
    },
]

INITIAL_STUDY_PATHS = [
    {
        "id": "sp_informatika",
        "code": "informatika",
        "title": "Informatika / Ilmu Komputer",
        "cluster": "Sains Komputasi & Rekayasa Perangkat Lunak",
        "description": "Program studi rekayasa algoritma, arsitektur komputasi, pengembangan kecerdasan buatan, dan sains sistem digital.",
        "radar_weights": json.dumps({
            "digital-literacy": 0.35,
            "problem-solving": 0.35,
            "collaboration": 0.10,
            "creativity": 0.10,
            "communication": 0.05,
            "leadership": 0.05,
        }),
        "tag_weights": json.dumps({
            "web-development": 0.40,
            "problem-solving": 0.30,
            "research": 0.15,
            "digital-literacy": 0.15,
        }),
        "suggested_pathways": json.dumps([
            "S1 Teknik Informatika",
            "S1 Ilmu Komputer",
            "D4 Rekayasa Perangkat Lunak Aplikasi",
        ]),
        "sort_order": 1,
    },
    {
        "id": "sp_sistem_informasi",
        "code": "sistem-informasi",
        "title": "Sistem Informasi & Bisnis Digital",
        "cluster": "Manajemen Sistem Informasi Terpadu",
        "description": "Program studi integrasi teknologi digital dengan proses bisnis organisasi, manajemen data, dan perancangan sistem informasi.",
        "radar_weights": json.dumps({
            "digital-literacy": 0.25,
            "problem-solving": 0.25,
            "communication": 0.20,
            "collaboration": 0.15,
            "leadership": 0.10,
            "creativity": 0.05,
        }),
        "tag_weights": json.dumps({
            "web-development": 0.30,
            "data-analysis": 0.30,
            "teamwork": 0.20,
            "writing": 0.20,
        }),
        "suggested_pathways": json.dumps([
            "S1 Sistem Informasi",
            "S1 Bisnis Digital",
            "D4 Manajemen Informatika",
        ]),
        "sort_order": 2,
    },
    {
        "id": "sp_dkv",
        "code": "desain-komunikasi-visual",
        "title": "Desain Komunikasi Visual (DKV)",
        "cluster": "Seni Visual & Desain Interaktif",
        "description": "Program studi penciptaan bahasa visual branding, desain antarmuka interaktif, tipografi, dan media animasi.",
        "radar_weights": json.dumps({
            "creativity": 0.40,
            "communication": 0.20,
            "digital-literacy": 0.20,
            "collaboration": 0.10,
            "problem-solving": 0.05,
            "leadership": 0.05,
        }),
        "tag_weights": json.dumps({
            "ui-ux": 0.40,
            "graphic-design": 0.35,
            "video-editing": 0.15,
            "creativity": 0.10,
        }),
        "suggested_pathways": json.dumps([
            "S1 Desain Komunikasi Visual",
            "D4 Desain Grafis",
            "S1 Desain Media Interaktif",
        ]),
        "sort_order": 3,
    },
    {
        "id": "sp_sains_data",
        "code": "sains-data",
        "title": "Sains Data / Statistika Terapan",
        "cluster": "Matematika Komputasi & Sains Data",
        "description": "Program studi pemodelan statistik matematis, analitika data skala besar, visualisasi analitis, dan riset data ilmiah.",
        "radar_weights": json.dumps({
            "problem-solving": 0.40,
            "digital-literacy": 0.30,
            "creativity": 0.10,
            "communication": 0.10,
            "collaboration": 0.05,
            "leadership": 0.05,
        }),
        "tag_weights": json.dumps({
            "data-analysis": 0.50,
            "research": 0.30,
            "problem-solving": 0.20,
        }),
        "suggested_pathways": json.dumps([
            "S1 Sains Data",
            "S1 Statistika",
            "D4 Analisis Data Terapan",
        ]),
        "sort_order": 4,
    },
    {
        "id": "sp_teknik_komputer",
        "code": "teknik-komputer",
        "title": "Teknik Komputer & Jaringan",
        "cluster": "Rekayasa Sistem Komputer & IoT",
        "description": "Program studi sistem terbenam (embedded systems), perancangan jaringan komputer, perangkat keras, dan integrasi IoT.",
        "radar_weights": json.dumps({
            "problem-solving": 0.35,
            "digital-literacy": 0.35,
            "creativity": 0.10,
            "collaboration": 0.10,
            "leadership": 0.05,
            "communication": 0.05,
        }),
        "tag_weights": json.dumps({
            "digital-literacy": 0.40,
            "problem-solving": 0.30,
            "research": 0.20,
            "teamwork": 0.10,
        }),
        "suggested_pathways": json.dumps([
            "S1 Teknik Komputer",
            "D4 Jaringan Komputer & Siber",
            "S1 Teknik Elektro (Konsentrasi Komputer)",
        ]),
        "sort_order": 5,
    },
    {
        "id": "sp_ilmu_komunikasi",
        "code": "ilmu-komunikasi",
        "title": "Ilmu Komunikasi & Media Digital",
        "cluster": "Sosial Humaniora & Komunikasi Massa",
        "description": "Program studi dinamika komunikasi publik, produksi pesan digital, jurnalisme multimedia, dan strategi relasi institusi.",
        "radar_weights": json.dumps({
            "communication": 0.40,
            "collaboration": 0.20,
            "creativity": 0.15,
            "leadership": 0.15,
            "digital-literacy": 0.05,
            "problem-solving": 0.05,
        }),
        "tag_weights": json.dumps({
            "public-speaking": 0.35,
            "writing": 0.35,
            "teamwork": 0.15,
            "event-management": 0.15,
        }),
        "suggested_pathways": json.dumps([
            "S1 Ilmu Komunikasi",
            "S1 Hubungan Masyarakat",
            "D4 Produksi Media",
        ]),
        "sort_order": 6,
    },
]


def upgrade() -> None:
    now = datetime.now(timezone.utc)

    # 1. Create career_paths table
    career_paths_table = op.create_table(
        'career_paths',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('cluster', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('radar_weights', sa.Text(), nullable=False),
        sa.Column('tag_weights', sa.Text(), nullable=False),
        sa.Column('suggested_pathways', sa.Text(), nullable=False),
        sa.Column('catalog_version', sa.String(length=64), nullable=False, server_default='career-catalog-v1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_career_paths_code', 'career_paths', ['code'], unique=True)
    op.create_index('ix_career_paths_active_sort', 'career_paths', ['is_active', 'sort_order'])

    # 2. Create study_paths table
    study_paths_table = op.create_table(
        'study_paths',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('cluster', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('radar_weights', sa.Text(), nullable=False),
        sa.Column('tag_weights', sa.Text(), nullable=False),
        sa.Column('suggested_pathways', sa.Text(), nullable=False),
        sa.Column('catalog_version', sa.String(length=64), nullable=False, server_default='career-catalog-v1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_study_paths_code', 'study_paths', ['code'], unique=True)
    op.create_index('ix_study_paths_active_sort', 'study_paths', ['is_active', 'sort_order'])

    # Seed initial career paths
    career_rows = [
        {
            **item,
            "catalog_version": "career-catalog-v1",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        for item in INITIAL_CAREER_PATHS
    ]
    op.bulk_insert(career_paths_table, career_rows)

    # Seed initial study paths
    study_rows = [
        {
            **item,
            "catalog_version": "career-catalog-v1",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        for item in INITIAL_STUDY_PATHS
    ]
    op.bulk_insert(study_paths_table, study_rows)


def downgrade() -> None:
    op.drop_index('ix_study_paths_active_sort', table_name='study_paths')
    op.drop_index('ix_study_paths_code', table_name='study_paths')
    op.drop_table('study_paths')

    op.drop_index('ix_career_paths_active_sort', table_name='career_paths')
    op.drop_index('ix_career_paths_code', table_name='career_paths')
    op.drop_table('career_paths')
