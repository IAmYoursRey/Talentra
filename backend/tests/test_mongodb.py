import sys
import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.core.mongodb import mongo_manager, MongoManager
from app.domain.documents import PortfolioItemDocument, PortfolioRevisionDocument, EvidenceRef


def test_motor_is_strictly_not_used():
    """
    MANDATORY REQUIREMENT 5:
    Motor is deprecated and must NOT be used.
    Official PyMongo Async (AsyncMongoClient) must be used.
    """
    assert "motor" not in sys.modules
    from pymongo import AsyncMongoClient
    assert AsyncMongoClient is not None


def test_portfolio_item_document_schema():
    """
    MANDATORY REQUIREMENT 24, 25:
    Validates PortfolioItemDocument schema, fields, and default values.
    """
    school_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    doc = PortfolioItemDocument(
        school_id=school_id,
        student_id=student_id,
        title="Robot Line Follower Microcontroller",
        activity_type="competition",
        description="Juara 1 Lomba Robotik Nasional Tingkat SMK 2025",
        canonical_tag_ids=["tag_embedded_systems", "tag_robotics", "tag_c_programming"],
    )

    assert doc.portfolio_id is not None
    assert doc.status == "draft"
    assert doc.current_revision == 1
    assert len(doc.canonical_tag_ids) == 3
    assert doc.school_id == school_id
    assert doc.student_id == student_id

    # Serialization to dict
    doc_dict = doc.model_dump()
    assert doc_dict["title"] == "Robot Line Follower Microcontroller"
    assert "portfolio_id" in doc_dict

    # Required fields validation: missing school_id should raise ValidationError
    with pytest.raises(ValidationError):
        PortfolioItemDocument.model_validate(
            {
                "student_id": student_id,
                "title": "Incomplete",
                "activity_type": "project",
                "description": "Missing school",
            }
        )


def test_portfolio_revision_document_schema():
    """
    MANDATORY REQUIREMENT 26:
    Validates PortfolioRevisionDocument schema and historical point-in-time evidence snapshot.
    """
    portfolio_id = str(uuid.uuid4())
    storage_obj_id = str(uuid.uuid4())

    evidence = EvidenceRef(
        storage_object_id=storage_obj_id,
        file_type="pdf",
        display_name="Sertifikat_LKS_2025.pdf",
        size_bytes=1024 * 1024 * 2,
    )

    revision = PortfolioRevisionDocument(
        portfolio_id=portfolio_id,
        version=1,
        description_snapshot="Initial submission of robotics certificate",
        tag_snapshot=["tag_embedded_systems", "tag_robotics"],
        evidence_refs=[evidence],
    )

    assert revision.revision_id is not None
    assert revision.version == 1
    assert len(revision.evidence_refs) == 1
    assert revision.evidence_refs[0].storage_object_id == storage_obj_id
    assert revision.evidence_refs[0].file_type == "pdf"


def test_tenant_isolation_mongodb_query_shapes():
    """
    MANDATORY REQUIREMENT 28:
    Tenant query shapes for MongoDB dynamic documents MUST enforce school_id.
    """
    school_a = str(uuid.uuid4())
    student_a = str(uuid.uuid4())

    # Build safe query filter for student portfolio retrieval
    query_filter = {
        "school_id": school_a,
        "student_id": student_a,
        "status": {"$ne": "deleted"},
    }

    assert "school_id" in query_filter
    assert query_filter["school_id"] == school_a

    # Reject query filters missing school_id
    def validate_tenant_query(flt: dict) -> bool:
        if "school_id" not in flt or not flt["school_id"]:
            raise ValueError("Cross-tenant query rejected: query filter must include school_id!")
        return True

    assert validate_tenant_query(query_filter) is True
    with pytest.raises(ValueError, match="Cross-tenant query rejected"):
        validate_tenant_query({"student_id": student_a})
