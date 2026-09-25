from typing import List, Optional, Tuple, Set
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..core.database import AsyncSessionLocal
from ..db.models import SkillTagModel


class SkillTagDTO(BaseModel):
    id: str
    code: str
    label: str
    category: str
    description: Optional[str] = None


# Default catalog matching Phase 1 canonical tags
CANONICAL_TAGS_DEFAULT: List[dict] = [
    {"id": "tag_web_development", "code": "web-development", "label": "Web Development", "category": "technical", "description": "Pengembangan aplikasi web modern"},
    {"id": "tag_ui_ux", "code": "ui-ux", "label": "UI/UX Design", "category": "creative", "description": "Desain antarmuka dan pengalaman pengguna"},
    {"id": "tag_problem_solving", "code": "problem-solving", "label": "Problem Solving", "category": "problem_solving", "description": "Pemecahan masalah dan logika algoritma"},
    {"id": "tag_leadership", "code": "leadership", "label": "Leadership", "category": "leadership", "description": "Kepemimpinan tim dan manajemen proyek"},
    {"id": "tag_teamwork", "code": "teamwork", "label": "Teamwork & Kolaborasi", "category": "collaboration", "description": "Kerja sama tim dalam menyelesaikan proyek"},
    {"id": "tag_public_speaking", "code": "public-speaking", "label": "Public Speaking", "category": "communication", "description": "Presentasi dan komunikasi verbal"},
    {"id": "tag_event_management", "code": "event-management", "label": "Event Management", "category": "leadership", "description": "Manajemen acara dan koordinasi kegiatan"},
    {"id": "tag_data_analysis", "code": "data-analysis", "label": "Data Analysis", "category": "technical", "description": "Pengolahan dan visualisasi data"},
    {"id": "tag_graphic_design", "code": "graphic-design", "label": "Graphic Design", "category": "creative", "description": "Desain grafis dan ilustrasi digital"},
    {"id": "tag_research", "code": "research", "label": "Research & Riset", "category": "problem_solving", "description": "Riset investigatif dan penulisan ilmiah"},
    {"id": "tag_writing", "code": "writing", "label": "Technical Writing", "category": "communication", "description": "Penulisan teknis dan dokumentasi"},
    {"id": "tag_video_editing", "code": "video-editing", "label": "Video Editing", "category": "creative", "description": "Penyuntingan video dan konten multimedia"},
    {"id": "tag_creativity", "code": "creativity", "label": "Kreativitas & Inovasi", "category": "creative", "description": "Inovasi karya dan solusi kreatif"},
    {"id": "tag_digital_literacy", "code": "digital-literacy", "label": "Digital Literacy", "category": "technical", "description": "Literasi digital dan etika siber"},
]


class SkillTagRepository:
    def __init__(self, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        self.session_factory = session_factory or AsyncSessionLocal

    async def list_active_tags(self) -> List[SkillTagDTO]:
        try:
            async with self.session_factory() as session:
                stmt = select(SkillTagModel).where(SkillTagModel.active.is_(True)).order_by(SkillTagModel.sort_order.asc())
                result = await session.execute(stmt)
                models = result.scalars().all()
                if models:
                    return [
                        SkillTagDTO(
                            id=m.id,
                            code=m.code,
                            label=m.display_name,
                            category=m.category,
                            description=m.description,
                        )
                        for m in models
                    ]
        except Exception:
            pass

        # Fallback to in-memory catalog
        return [SkillTagDTO(**t) for t in CANONICAL_TAGS_DEFAULT]

    async def validate_tags(self, tag_identifiers: List[str]) -> Tuple[bool, List[str], Optional[str]]:
        """
        Validates that tag identifiers:
        1. Count is between 3 and 5.
        2. Are unique (no duplicates).
        3. All exist in canonical active catalog (either by id or code).
        Returns: (is_valid, normalized_tag_ids, error_message)
        """
        if not tag_identifiers:
            return False, [], "Portofolio wajib memiliki minimal 3 dan maksimal 5 tag kapabilitas."

        # Unique validation
        unique_input = []
        seen = set()
        for t in tag_identifiers:
            clean = t.strip()
            if clean in seen:
                return False, [], f"Tag '{clean}' duplikat. Setiap tag kapabilitas hanya boleh dipilih satu kali."
            seen.add(clean)
            unique_input.append(clean)

        if len(unique_input) < 3:
            return False, [], f"Jumlah tag ({len(unique_input)}) kurang dari batas minimal 3 tag."
        if len(unique_input) > 5:
            return False, [], f"Jumlah tag ({len(unique_input)}) melebihi batas maksimal 5 tag."

        active_tags = await self.list_active_tags()
        valid_map: dict[str, str] = {}  # maps both id and code to canonical id
        for tag in active_tags:
            valid_map[tag.id] = tag.id
            valid_map[tag.code] = tag.id

        normalized_ids: List[str] = []
        for t in unique_input:
            if t not in valid_map:
                return False, [], f"Tag '{t}' bukan merupakan tag kapabilitas kanonikal yang valid."
            normalized_ids.append(valid_map[t])

        return True, normalized_ids, None
