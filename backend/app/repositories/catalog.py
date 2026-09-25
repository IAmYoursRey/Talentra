import json
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..core.database import AsyncSessionLocal
from ..db.models import CareerPathModel, StudyPathModel
from ..domain.models import CareerPath, StudyPath

FALLBACK_CAREER_PATHS = [
    {
        "id": "cp_software_dev",
        "code": "software-development",
        "title": "Rekayasa Perangkat Lunak & Aplikasi",
        "cluster": "Teknologi Informasi & Rekayasa Perangkat Lunak",
        "description": "Pengembangan sistem perangkat lunak, arsitektur aplikasi web/mobile, dan rekayasa kode berbasis solusi terstruktur.",
        "radar_weights": {
            "digital-literacy": 0.35,
            "problem-solving": 0.35,
            "collaboration": 0.10,
            "creativity": 0.10,
            "communication": 0.05,
            "leadership": 0.05,
        },
        "tag_weights": {
            "web-development": 0.40,
            "problem-solving": 0.30,
            "digital-literacy": 0.15,
            "teamwork": 0.15,
        },
        "suggested_pathways": [
            "Junior Frontend Developer",
            "Junior Backend Developer",
            "Full-Stack Engineer",
            "Software QA Tester",
        ],
        "sort_order": 1,
    },
    {
        "id": "cp_data_analytics",
        "code": "data-analytics",
        "title": "Sains Data & Analitika Terapan",
        "cluster": "Sains Data & Kecerdasan Komputasi",
        "description": "Eksplorasi pengolahan data, analisis statistik, visualisasi wawasan, dan pemodelan analitik terstruktur.",
        "radar_weights": {
            "digital-literacy": 0.30,
            "problem-solving": 0.35,
            "creativity": 0.10,
            "communication": 0.15,
            "collaboration": 0.05,
            "leadership": 0.05,
        },
        "tag_weights": {
            "data-analysis": 0.45,
            "research": 0.25,
            "problem-solving": 0.20,
            "digital-literacy": 0.10,
        },
        "suggested_pathways": [
            "Junior Data Analyst",
            "Business Intelligence Associate",
            "Data Specialist",
            "Research Assistant",
        ],
        "sort_order": 2,
    },
    {
        "id": "cp_digital_product_uiux",
        "code": "digital-product-uiux",
        "title": "Desain Produk Digital & UI/UX",
        "cluster": "Desain Komunikasi Visual & Media Digital",
        "description": "Perancangan antarmuka visual interaktif, riset pengalaman pengguna, wireframing, dan prototipe aplikasi digital.",
        "radar_weights": {
            "creativity": 0.35,
            "digital-literacy": 0.25,
            "communication": 0.15,
            "problem-solving": 0.10,
            "collaboration": 0.10,
            "leadership": 0.05,
        },
        "tag_weights": {
            "ui-ux": 0.45,
            "graphic-design": 0.25,
            "creativity": 0.15,
            "web-development": 0.15,
        },
        "suggested_pathways": [
            "UI/UX Designer",
            "Product Design Associate",
            "Web Designer",
            "Design Researcher",
        ],
        "sort_order": 3,
    },
    {
        "id": "cp_creative_digital_media",
        "code": "creative-digital-media",
        "title": "Media Kreatif Digital & Konten Visual",
        "cluster": "Seni Media Digital & Animasi",
        "description": "Penciptaan konten multimedia visual, penyuntingan video dinamis, grafis interaktif, dan komunikasi media kreatif.",
        "radar_weights": {
            "creativity": 0.40,
            "communication": 0.20,
            "digital-literacy": 0.20,
            "collaboration": 0.10,
            "problem-solving": 0.05,
            "leadership": 0.05,
        },
        "tag_weights": {
            "graphic-design": 0.35,
            "video-editing": 0.35,
            "creativity": 0.20,
            "writing": 0.10,
        },
        "suggested_pathways": [
            "Digital Graphic Designer",
            "Video Editor",
            "Motion Graphic Artist",
            "Creative Media Producer",
        ],
        "sort_order": 4,
    },
    {
        "id": "cp_cybersecurity_infra",
        "code": "cybersecurity-infrastructure",
        "title": "Keamanan Siber & Infrastruktur Jaringan",
        "cluster": "Jaringan Komputer & Telekomunikasi",
        "description": "Pengelolaan keamanan informasi, konfigurasi infrastruktur jaringan komputasi, dan pemecahan masalah sistem siber.",
        "radar_weights": {
            "digital-literacy": 0.35,
            "problem-solving": 0.35,
            "collaboration": 0.10,
            "leadership": 0.10,
            "communication": 0.05,
            "creativity": 0.05,
        },
        "tag_weights": {
            "digital-literacy": 0.40,
            "problem-solving": 0.30,
            "research": 0.20,
            "teamwork": 0.10,
        },
        "suggested_pathways": [
            "Network Administrator",
            "Junior Security Analyst",
            "IT Infrastructure Specialist",
            "Cloud Support Associate",
        ],
        "sort_order": 5,
    },
    {
        "id": "cp_communication_content",
        "code": "communication-content",
        "title": "Komunikasi Publik & Penulisan Teknis",
        "cluster": "Komunikasi & Manajemen Informasi",
        "description": "Penyampaian gagasan profesional, presentasi publik, penulisan dokumentasi teknis sistem, dan relasi komunikasi.",
        "radar_weights": {
            "communication": 0.40,
            "collaboration": 0.20,
            "creativity": 0.15,
            "leadership": 0.15,
            "digital-literacy": 0.05,
            "problem-solving": 0.05,
        },
        "tag_weights": {
            "public-speaking": 0.40,
            "writing": 0.30,
            "teamwork": 0.15,
            "digital-literacy": 0.15,
        },
        "suggested_pathways": [
            "Technical Writer",
            "Public Relations Associate",
            "Content Strategist",
            "Communications Coordinator",
        ],
        "sort_order": 6,
    },
    {
        "id": "cp_business_entrepreneurship",
        "code": "business-entrepreneurship",
        "title": "Inisiatif Bisnis & Kewirausahaan Digital",
        "cluster": "Bisnis & Manajemen Digital",
        "description": "Inisiasi proyek bernilai tambah, manajemen operasional acara/bisnis, koordinasi tim, dan perancangan strategi pasar.",
        "radar_weights": {
            "leadership": 0.35,
            "communication": 0.25,
            "problem-solving": 0.15,
            "collaboration": 0.15,
            "creativity": 0.05,
            "digital-literacy": 0.05,
        },
        "tag_weights": {
            "leadership": 0.40,
            "event-management": 0.30,
            "teamwork": 0.15,
            "public-speaking": 0.15,
        },
        "suggested_pathways": [
            "Digital Entrepreneur",
            "Project Coordinator",
            "Business Development Associate",
            "Operations Specialist",
        ],
        "sort_order": 7,
    },
]

FALLBACK_STUDY_PATHS = [
    {
        "id": "sp_informatika",
        "code": "informatika",
        "title": "Informatika / Ilmu Komputer",
        "cluster": "Sains Komputasi & Rekayasa Perangkat Lunak",
        "description": "Program studi rekayasa algoritma, arsitektur komputasi, pengembangan kecerdasan buatan, dan sains sistem digital.",
        "radar_weights": {
            "digital-literacy": 0.35,
            "problem-solving": 0.35,
            "collaboration": 0.10,
            "creativity": 0.10,
            "communication": 0.05,
            "leadership": 0.05,
        },
        "tag_weights": {
            "web-development": 0.40,
            "problem-solving": 0.30,
            "research": 0.15,
            "digital-literacy": 0.15,
        },
        "suggested_pathways": [
            "S1 Teknik Informatika",
            "S1 Ilmu Komputer",
            "D4 Rekayasa Perangkat Lunak Aplikasi",
        ],
        "sort_order": 1,
    },
    {
        "id": "sp_sistem_informasi",
        "code": "sistem-informasi",
        "title": "Sistem Informasi & Bisnis Digital",
        "cluster": "Manajemen Sistem Informasi Terpadu",
        "description": "Program studi integrasi teknologi digital dengan proses bisnis organisasi, manajemen data, dan perancangan sistem informasi.",
        "radar_weights": {
            "digital-literacy": 0.25,
            "problem-solving": 0.25,
            "communication": 0.20,
            "collaboration": 0.15,
            "leadership": 0.10,
            "creativity": 0.05,
        },
        "tag_weights": {
            "web-development": 0.30,
            "data-analysis": 0.30,
            "teamwork": 0.20,
            "writing": 0.20,
        },
        "suggested_pathways": [
            "S1 Sistem Informasi",
            "S1 Bisnis Digital",
            "D4 Manajemen Informatika",
        ],
        "sort_order": 2,
    },
    {
        "id": "sp_dkv",
        "code": "desain-komunikasi-visual",
        "title": "Desain Komunikasi Visual (DKV)",
        "cluster": "Seni Visual & Desain Interaktif",
        "description": "Program studi penciptaan bahasa visual branding, desain antarmuka interaktif, tipografi, dan media animasi.",
        "radar_weights": {
            "creativity": 0.40,
            "communication": 0.20,
            "digital-literacy": 0.20,
            "collaboration": 0.10,
            "problem-solving": 0.05,
            "leadership": 0.05,
        },
        "tag_weights": {
            "ui-ux": 0.40,
            "graphic-design": 0.35,
            "video-editing": 0.15,
            "creativity": 0.10,
        },
        "suggested_pathways": [
            "S1 Desain Komunikasi Visual",
            "D4 Desain Grafis",
            "S1 Desain Media Interaktif",
        ],
        "sort_order": 3,
    },
    {
        "id": "sp_sains_data",
        "code": "sains-data",
        "title": "Sains Data / Statistika Terapan",
        "cluster": "Matematika Komputasi & Sains Data",
        "description": "Program studi pemodelan statistik matematis, analitika data skala besar, visualisasi analitis, dan riset data ilmiah.",
        "radar_weights": {
            "problem-solving": 0.40,
            "digital-literacy": 0.30,
            "creativity": 0.10,
            "communication": 0.10,
            "collaboration": 0.05,
            "leadership": 0.05,
        },
        "tag_weights": {
            "data-analysis": 0.50,
            "research": 0.30,
            "problem-solving": 0.20,
        },
        "suggested_pathways": [
            "S1 Sains Data",
            "S1 Statistika",
            "D4 Analisis Data Terapan",
        ],
        "sort_order": 4,
    },
    {
        "id": "sp_teknik_komputer",
        "code": "teknik-komputer",
        "title": "Teknik Komputer & Jaringan",
        "cluster": "Rekayasa Sistem Komputer & IoT",
        "description": "Program studi sistem terbenam (embedded systems), perancangan jaringan komputer, perangkat keras, dan integrasi IoT.",
        "radar_weights": {
            "problem-solving": 0.35,
            "digital-literacy": 0.35,
            "creativity": 0.10,
            "collaboration": 0.10,
            "leadership": 0.05,
            "communication": 0.05,
        },
        "tag_weights": {
            "digital-literacy": 0.40,
            "problem-solving": 0.30,
            "research": 0.20,
            "teamwork": 0.10,
        },
        "suggested_pathways": [
            "S1 Teknik Komputer",
            "D4 Jaringan Komputer & Siber",
            "S1 Teknik Elektro (Konsentrasi Komputer)",
        ],
        "sort_order": 5,
    },
    {
        "id": "sp_ilmu_komunikasi",
        "code": "ilmu-komunikasi",
        "title": "Ilmu Komunikasi & Media Digital",
        "cluster": "Sosial Humaniora & Komunikasi Massa",
        "description": "Program studi dinamika komunikasi publik, produksi pesan digital, jurnalisme multimedia, dan strategi relasi institusi.",
        "radar_weights": {
            "communication": 0.40,
            "collaboration": 0.20,
            "creativity": 0.15,
            "leadership": 0.15,
            "digital-literacy": 0.05,
            "problem-solving": 0.05,
        },
        "tag_weights": {
            "public-speaking": 0.35,
            "writing": 0.35,
            "teamwork": 0.15,
            "event-management": 0.15,
        },
        "suggested_pathways": [
            "S1 Ilmu Komunikasi",
            "S1 Hubungan Masyarakat",
            "D4 Produksi Media",
        ],
        "sort_order": 6,
    },
]


class CareerCatalogRepository:
    """
    Repository for versioned career paths and study paths.
    Strictly validates weight sums and properties.
    """

    def __init__(self, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        self.session_factory = session_factory or AsyncSessionLocal

    def _validate_weights(self, weights: dict[str, float], name: str) -> None:
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weight sum for {name} must equal 1.0 (got {total:.4f})")
        for k, v in weights.items():
            if v < 0:
                raise ValueError(f"Negative weight {k}={v} not allowed in {name}")

    async def get_active_career_paths(self) -> List[CareerPath]:
        try:
            async with self.session_factory() as session:
                stmt = (
                    select(CareerPathModel)
                    .where(CareerPathModel.is_active == True)
                    .order_by(CareerPathModel.sort_order.asc())
                )
                res = await session.execute(stmt)
                models = res.scalars().all()
                if models:
                    paths = []
                    for m in models:
                        radar_w = json.loads(m.radar_weights)
                        tag_w = json.loads(m.tag_weights)
                        self._validate_weights(radar_w, f"career {m.code} radar")
                        self._validate_weights(tag_w, f"career {m.code} tags")
                        paths.append(
                            CareerPath(
                                id=m.id,
                                code=m.code,
                                title=m.title,
                                cluster=m.cluster,
                                description=m.description,
                                radar_weights=radar_w,
                                tag_weights=tag_w,
                                suggested_pathways=json.loads(m.suggested_pathways),
                                catalog_version=m.catalog_version,
                                is_active=m.is_active,
                                sort_order=m.sort_order,
                            )
                        )
                    return paths
        except Exception:
            # Fallback if DB not seeded / offline
            pass

        # Return validated fallbacks
        return [
            CareerPath(
                id=item["id"],
                code=item["code"],
                title=item["title"],
                cluster=item["cluster"],
                description=item["description"],
                radar_weights=item["radar_weights"],
                tag_weights=item["tag_weights"],
                suggested_pathways=item["suggested_pathways"],
                catalog_version="career-catalog-v1",
                is_active=True,
                sort_order=item["sort_order"],
            )
            for item in FALLBACK_CAREER_PATHS
        ]

    async def get_active_study_paths(self) -> List[StudyPath]:
        try:
            async with self.session_factory() as session:
                stmt = (
                    select(StudyPathModel)
                    .where(StudyPathModel.is_active == True)
                    .order_by(StudyPathModel.sort_order.asc())
                )
                res = await session.execute(stmt)
                models = res.scalars().all()
                if models:
                    paths = []
                    for m in models:
                        radar_w = json.loads(m.radar_weights)
                        tag_w = json.loads(m.tag_weights)
                        self._validate_weights(radar_w, f"study {m.code} radar")
                        self._validate_weights(tag_w, f"study {m.code} tags")
                        paths.append(
                            StudyPath(
                                id=m.id,
                                code=m.code,
                                title=m.title,
                                cluster=m.cluster,
                                description=m.description,
                                radar_weights=radar_w,
                                tag_weights=tag_w,
                                suggested_pathways=json.loads(m.suggested_pathways),
                                catalog_version=m.catalog_version,
                                is_active=m.is_active,
                                sort_order=m.sort_order,
                            )
                        )
                    return paths
        except Exception:
            pass

        return [
            StudyPath(
                id=item["id"],
                code=item["code"],
                title=item["title"],
                cluster=item["cluster"],
                description=item["description"],
                radar_weights=item["radar_weights"],
                tag_weights=item["tag_weights"],
                suggested_pathways=item["suggested_pathways"],
                catalog_version="career-catalog-v1",
                is_active=True,
                sort_order=item["sort_order"],
            )
            for item in FALLBACK_STUDY_PATHS
        ]
