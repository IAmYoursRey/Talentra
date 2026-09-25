import uuid
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class EvidenceRef(BaseModel):
    type: str = "file"  # "file" or "external_link"
    storage_object_id: Optional[str] = None
    url: Optional[str] = None
    label: Optional[str] = None
    display_name: str = ""
    file_type: Optional[str] = None  # pdf, image, video, link
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None


class PortfolioItemDocument(BaseModel):
    """
    MongoDB Document Schema for portfolio_items.
    PostgreSQL holds identity, role, and student enrollment facts;
    MongoDB holds the dynamic evidence payloads.
    """
    portfolio_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    school_id: str
    student_id: str
    title: str
    activity_type: str
    activity_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    description: str
    canonical_tag_ids: List[str] = Field(default_factory=list)
    evidence_refs: List[EvidenceRef] = Field(default_factory=list)
    status: str = "draft"  # draft, submitted, revision_requested, approved, rejected
    current_revision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    current_revision: int = 1
    current_revision_number: int = 1
    teacher_feedback: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    submitted_at: Optional[datetime] = None


class PortfolioRevisionDocument(BaseModel):
    """
    MongoDB Document Schema for portfolio_revisions.
    Preserves point-in-time snapshots for teacher validation history.
    Immutable once submitted.
    """
    revision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    portfolio_id: str
    school_id: str = ""
    student_id: str = ""
    version: int = 1
    title_snapshot: str = ""
    activity_type_snapshot: str = ""
    description_snapshot: str = ""
    tag_snapshot: List[str] = Field(default_factory=list)
    evidence_refs: List[EvidenceRef] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    submitted_at: Optional[datetime] = None


class EvidenceTagSnapshotDocument(BaseModel):
    """
    MongoDB Document Schema for evidence_tag_snapshots.
    Immutable projection created upon teacher approval.
    Powers deterministic student skill radar without querying raw unapproved documents.
    """
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    school_id: str
    student_id: str
    portfolio_id: str
    revision_id: str
    validation_decision_id: str
    canonical_tag_ids: List[str] = Field(default_factory=list)
    canonical_tag_codes: List[str] = Field(default_factory=list)
    approved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    projection_version: str = "v1"


class RecommendationSnapshotDocument(BaseModel):
    """
    MongoDB Document Schema for recommendation_snapshots.
    Preserves immutable, versioned recommendation state and provenance.
    """
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    school_id: str
    student_id: str
    source_fingerprint: str
    catalog_version: str = "career-catalog-v1"
    scoring_version: str = "recommendation-v1"
    mapping_version: str = "mapping-v1"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_confidence: dict = Field(default_factory=dict)
    career_results: List[dict] = Field(default_factory=list)
    study_results: List[dict] = Field(default_factory=list)
    supporting_approval_ids: List[str] = Field(default_factory=list)


class DerivedProfessionalDescriptionDocument(BaseModel):
    """
    MongoDB Document Schema for derived professional descriptions.
    Stores professional transformed text separately from immutable portfolio revision.
    """
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    school_id: str
    student_id: str
    portfolio_id: str
    revision_id: str
    source_hash: str
    original_title: str = ""
    professional_text: str = ""
    translator_version: str = "industry-language-v1"
    mode: str = "deterministic"  # "deterministic" or "llm"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CVContentSnapshotDocument(BaseModel):
    """
    MongoDB Document Schema for cv_content_snapshots.
    Preserves immutable, point-in-time snapshot of approved student data,
    selected portfolios, skills, rubric dimension summaries, and optional exploration interests.
    Once issued, contents are strictly immutable.
    """
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    school_id: str
    student_id: str
    snapshot_version: str = "cv-snapshot-v1"
    renderer_version: str = "cv-pdf-v1"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "issued"  # preparing, issued, revoked, failed

    # Profile & Identity (No national identifiers!)
    profile: dict = Field(default_factory=dict)
    # Approved Skills (Evidence-backed radar & strengths)
    approved_skills: List[dict] = Field(default_factory=list)
    # Teacher Validated Competencies (Aggregated dimension observations, no private teacher ID/feedback)
    teacher_validated_competencies: List[dict] = Field(default_factory=list)
    # Selected Approved Portfolios
    selected_portfolios: List[dict] = Field(default_factory=list)
    # Optional Exploration Summary (Default None)
    optional_exploration_summary: Optional[dict] = None

    # Canonical SHA-256 Digest of the snapshot content
    content_digest: str = ""

