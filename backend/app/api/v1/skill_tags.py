from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...repositories.skill_tag import SkillTagRepository, SkillTagDTO

router = APIRouter(prefix="/skill-tags", tags=["Skill Tags"])

_skill_tag_repo = SkillTagRepository()


def get_skill_tag_repo() -> SkillTagRepository:
    return _skill_tag_repo


class SkillTagsResponse(BaseModel):
    items: List[SkillTagDTO]


@router.get("", response_model=SkillTagsResponse)
async def list_canonical_skill_tags(
    tag_repo: SkillTagRepository = Depends(get_skill_tag_repo),
):
    """
    Returns the backend-controlled active canonical skill tags catalog.
    Used by student portfolio creation and teacher review tag validation.
    """
    tags = await tag_repo.list_active_tags()
    return SkillTagsResponse(items=tags)
