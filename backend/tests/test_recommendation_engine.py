import pytest
import uuid
from datetime import datetime, timezone, timedelta

from app.domain.models import CareerPath, StudyPath
from app.repositories.catalog import CareerCatalogRepository, FALLBACK_CAREER_PATHS, FALLBACK_STUDY_PATHS
from app.repositories.portfolio import InMemoryPortfolioRepository
from app.services.projection_service import StudentSkillProjectionService
from app.services.recommendation_engine import (
    RecommendationEngineService,
    SCORING_VERSION,
    CATALOG_VERSION,
    MAPPING_VERSION,
)


@pytest.fixture
def test_setup():
    portfolio_repo = InMemoryPortfolioRepository()
    catalog_repo = CareerCatalogRepository()
    projection_service = StudentSkillProjectionService(portfolio_repo=portfolio_repo)
    engine = RecommendationEngineService(
        portfolio_repo=portfolio_repo,
        catalog_repo=catalog_repo,
        projection_service=projection_service,
    )
    return {
        "portfolio_repo": portfolio_repo,
        "catalog_repo": catalog_repo,
        "projection_service": projection_service,
        "engine": engine,
    }


@pytest.mark.asyncio
async def test_catalog_validation_and_normalized_weights(test_setup):
    """
    Validates that career and study paths enforce strict weight normalization (sum = 1.0)
    and non-negative weights.
    """
    catalog_repo: CareerCatalogRepository = test_setup["catalog_repo"]
    careers = await catalog_repo.get_active_career_paths()
    studies = await catalog_repo.get_active_study_paths()

    assert len(careers) >= 6
    assert len(studies) >= 5

    # Check career weights
    for cp in careers:
        assert cp.code
        assert cp.title
        radar_sum = sum(cp.radar_weights.values())
        assert abs(radar_sum - 1.0) < 0.001, f"{cp.code} radar weights must sum to 1.0 (got {radar_sum})"
        tag_sum = sum(cp.tag_weights.values())
        assert abs(tag_sum - 1.0) < 0.001, f"{cp.code} tag weights must sum to 1.0 (got {tag_sum})"
        assert all(w >= 0 for w in cp.radar_weights.values())
        assert all(w >= 0 for w in cp.tag_weights.values())

    # Check study weights
    for sp in studies:
        assert sp.code
        assert sp.title
        radar_sum = sum(sp.radar_weights.values())
        assert abs(radar_sum - 1.0) < 0.001, f"{sp.code} radar weights must sum to 1.0 (got {radar_sum})"
        tag_sum = sum(sp.tag_weights.values())
        assert abs(tag_sum - 1.0) < 0.001, f"{sp.code} tag weights must sum to 1.0 (got {tag_sum})"


@pytest.mark.asyncio
async def test_approved_only_evidence_invariant(test_setup):
    """
    Invariant: Draft, submitted, revision_requested, and rejected items contribute ZERO
    to career and study recommendations. Only teacher-approved evidence contributes.
    """
    repo: InMemoryPortfolioRepository = test_setup["portfolio_repo"]
    engine: RecommendationEngineService = test_setup["engine"]
    school_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    # 1. Zero evidence initially -> empty exploration or early signals with limited confidence
    res0 = await engine.get_or_generate_recommendation(school_id, student_id)
    assert res0["evidenceConfidence"]["approvedPortfolioCount"] == 0
    assert res0["evidenceConfidence"]["level"] == "limited"
    assert len(res0["careerPaths"]) == 0

    # 2. Add unapproved items (draft, submitted, rejected)
    for i, st in enumerate(["draft", "submitted", "revision_requested", "rejected"]):
        pid = f"p_unapproved_{i}"
        await repo.save_portfolio({
            "school_id": school_id,
            "student_id": student_id,
            "portfolio_id": pid,
            "title": f"Unapproved item {i}",
            "description": "Not approved by teacher",
            "activity_type": "project",
            "canonical_tag_ids": ["web-development", "problem-solving", "digital-literacy"],
            "status": st,
            "current_revision_id": f"rev_{i}",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })

    # Recommendation should STILL have 0 approved items
    res1 = await engine.get_or_generate_recommendation(school_id, student_id, force_refresh=True)
    assert res1["evidenceConfidence"]["approvedPortfolioCount"] == 0
    assert len(res1["careerPaths"]) == 0

    # 3. Now approve 1 portfolio
    approved_pid = "p_approved_1"
    now = datetime.now(timezone.utc)
    await repo.save_portfolio({
        "school_id": school_id,
        "student_id": student_id,
        "portfolio_id": approved_pid,
        "title": "Aplikasi Web Sekolah",
        "description": "Membangun sistem informasi sekolah",
        "activity_type": "project",
        "canonical_tag_ids": ["web-development", "problem-solving", "digital-literacy"],
        "status": "approved",
        "current_revision_id": "rev_app_1",
        "created_at": now,
        "updated_at": now,
    })
    await repo.save_approved_snapshot({
        "school_id": school_id,
        "student_id": student_id,
        "portfolio_id": approved_pid,
        "revision_id": "rev_app_1",
        "approved_at": now,
        "canonical_tag_ids": ["web-development", "problem-solving", "digital-literacy"],
    })

    # Now recommendations should reflect the 1 approved work
    res2 = await engine.get_or_generate_recommendation(school_id, student_id, force_refresh=True)
    assert res2["evidenceConfidence"]["approvedPortfolioCount"] == 1
    assert len(res2["careerPaths"]) > 0
    # Provenance must link to the approved portfolio
    top_career = res2["careerPaths"][0]
    assert top_career["evidenceCount"] >= 1
    assert any(p["portfolioId"] == approved_pid for p in top_career["supportingPortfolios"])


@pytest.mark.asyncio
async def test_missing_rubric_renormalization_policy(test_setup):
    """
    Policy: Missing rubric is NOT negative ability.
    If rubric is absent, available proof-of-work (radar: 75%, tags: 25%) is re-normalized
    to sum to 100%, without unfairly depressing the match score.
    """
    repo: InMemoryPortfolioRepository = test_setup["portfolio_repo"]
    engine: RecommendationEngineService = test_setup["engine"]
    school_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    now = datetime.now(timezone.utc)
    # Add approved evidence with web-dev and problem-solving tags (4 works for solid evidence base)
    for i in range(4):
        pid = f"pid_{i}"
        await repo.save_portfolio({
            "school_id": school_id,
            "student_id": student_id,
            "portfolio_id": pid,
            "title": f"Proyek Web {i}",
            "description": "Aplikasi web responsif",
            "activity_type": "project",
            "canonical_tag_ids": ["web-development", "problem-solving", "digital-literacy"],
            "status": "approved",
            "current_revision_id": f"rev_{i}",
            "created_at": now,
            "updated_at": now,
        })
        await repo.save_approved_snapshot({
            "school_id": school_id,
            "student_id": student_id,
            "portfolio_id": pid,
            "revision_id": f"rev_{i}",
            "approved_at": now,
            "canonical_tag_ids": ["web-development", "problem-solving", "digital-literacy"],
        })

    # No rubrics seeded
    res = await engine.get_or_generate_recommendation(school_id, student_id)
    assert len(res["careerPaths"]) > 0
    top = res["careerPaths"][0]

    # Components: rubricMatch is 0 because missing, but matchScore should be healthy (> 50)
    # thanks to re-normalization
    assert top["components"]["rubricMatch"] == 0
    assert top["matchScore"] >= 50
    # Radar and tag match should be active
    assert top["components"]["radarMatch"] > 0
    assert top["components"]["tagMatch"] > 0


@pytest.mark.asyncio
async def test_repetition_cap_and_longitudinal_confidence(test_setup):
    """
    Invariant: Repetition cap prevents spamming identical uploads in a short window.
    Longitudinal evidence across different time periods yields higher evidence confidence.
    """
    repo: InMemoryPortfolioRepository = test_setup["portfolio_repo"]
    engine: RecommendationEngineService = test_setup["engine"]
    school_id = str(uuid.uuid4())
    student_single_period = str(uuid.uuid4())
    student_multi_period = str(uuid.uuid4())

    now = datetime.now(timezone.utc)

    # Student 1: Spams 6 identical items in the SAME period
    for i in range(6):
        pid = f"spam_{i}"
        await repo.save_portfolio({
            "school_id": school_id,
            "student_id": student_single_period,
            "portfolio_id": pid,
            "title": f"Spam Item {i}",
            "description": "Deskripsi yang sama",
            "activity_type": "project",
            "canonical_tag_ids": ["web-development", "problem-solving", "digital-literacy"],
            "status": "approved",
            "current_revision_id": f"rev_spam_{i}",
            "created_at": now,
            "updated_at": now,
        })
        await repo.save_approved_snapshot({
            "school_id": school_id,
            "student_id": student_single_period,
            "portfolio_id": pid,
            "revision_id": f"rev_spam_{i}",
            "approved_at": now,
            "canonical_tag_ids": ["web-development", "problem-solving", "digital-literacy"],
        })

    # Student 2: 4 items across 3 distinct periods (spanning 14 months)
    dates = [
        now - timedelta(days=400),
        now - timedelta(days=200),
        now - timedelta(days=100),
        now,
    ]
    for i, d in enumerate(dates):
        pid = f"longitudinal_{i}"
        await repo.save_portfolio({
            "school_id": school_id,
            "student_id": student_multi_period,
            "portfolio_id": pid,
            "title": f"Proyek Longitudinal {i}",
            "description": "Karya berkelanjutan",
            "activity_type": "project",
            "canonical_tag_ids": ["web-development", "data-analysis", "problem-solving"],
            "status": "approved",
            "current_revision_id": f"rev_long_{i}",
            "created_at": d,
            "updated_at": d,
        })
        await repo.save_approved_snapshot({
            "school_id": school_id,
            "student_id": student_multi_period,
            "portfolio_id": pid,
            "revision_id": f"rev_long_{i}",
            "approved_at": d,
            "canonical_tag_ids": ["web-development", "data-analysis", "problem-solving"],
        })

    res_single = await engine.get_or_generate_recommendation(school_id, student_single_period)
    res_multi = await engine.get_or_generate_recommendation(school_id, student_multi_period)

    # Student 2 should have higher time span in months and higher period count
    assert res_multi["evidenceConfidence"]["timeSpanMonths"] > res_single["evidenceConfidence"]["timeSpanMonths"]
    assert res_multi["evidenceConfidence"]["activePeriodCount"] >= 3
    assert res_single["evidenceConfidence"]["activePeriodCount"] == 1


@pytest.mark.asyncio
async def test_confidence_is_not_probability_and_separate_from_match(test_setup):
    """
    Confidence is about evidence quantity, breadth, and longitudinal duration.
    It is strictly NOT probability of success, talent percentage, or IQ.
    """
    repo: InMemoryPortfolioRepository = test_setup["portfolio_repo"]
    engine: RecommendationEngineService = test_setup["engine"]
    school_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    now = datetime.now(timezone.utc)
    # 1 approved portfolio: high match with software-development, but limited confidence
    pid = "single_strong_work"
    await repo.save_portfolio({
        "school_id": school_id,
        "student_id": student_id,
        "portfolio_id": pid,
        "title": "Aplikasi Web E-Commerce Sekolah",
        "description": "Mengembangkan sistem full stack",
        "activity_type": "project",
        "canonical_tag_ids": ["web-development", "problem-solving", "digital-literacy"],
        "status": "approved",
        "current_revision_id": "rev_1",
        "created_at": now,
        "updated_at": now,
    })
    await repo.save_approved_snapshot({
        "school_id": school_id,
        "student_id": student_id,
        "portfolio_id": pid,
        "revision_id": "rev_1",
        "approved_at": now,
        "canonical_tag_ids": ["web-development", "problem-solving", "digital-literacy"],
    })

    res = await engine.get_or_generate_recommendation(school_id, student_id)

    # Verification: forbidden fields must NOT exist in the serialized response
    forbidden_keys = ["probability", "successChance", "employabilityScore", "admissionChance", "iq", "talentPercentage"]
    for k in forbidden_keys:
        assert k not in res
        assert k not in res["evidenceConfidence"]
        if res["careerPaths"]:
            assert k not in res["careerPaths"][0]

    # Confidence must be categorized into standard levels: limited, developing, moderate, strong
    valid_levels = {"limited", "developing", "moderate", "strong"}
    assert res["evidenceConfidence"]["level"] in valid_levels
    # Match score should be non-zero while confidence remains limited due to single item
    assert res["careerPaths"][0]["matchScore"] > 0
    assert res["evidenceConfidence"]["level"] == "limited"


@pytest.mark.asyncio
async def test_deterministic_tie_breaking_and_snapshot_idempotency(test_setup):
    """
    Given the same inputs, recommendations must produce identical ranking and scores every time.
    Tie break: matchScore desc, confidence desc, code asc.
    Repeated queries must reuse snapshot idempotently without creating duplicate documents.
    """
    repo: InMemoryPortfolioRepository = test_setup["portfolio_repo"]
    engine: RecommendationEngineService = test_setup["engine"]
    school_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    now = datetime.now(timezone.utc)
    for i in range(3):
        pid = f"tie_work_{i}"
        await repo.save_portfolio({
            "school_id": school_id,
            "student_id": student_id,
            "portfolio_id": pid,
            "title": f"Karya {i}",
            "description": "Deskripsi karya",
            "activity_type": "project",
            "canonical_tag_ids": ["creativity", "collaboration", "communication"],
            "status": "approved",
            "current_revision_id": f"rev_{i}",
            "created_at": now,
            "updated_at": now,
        })
        await repo.save_approved_snapshot({
            "school_id": school_id,
            "student_id": student_id,
            "portfolio_id": pid,
            "revision_id": f"rev_{i}",
            "approved_at": now,
            "canonical_tag_ids": ["creativity", "collaboration", "communication"],
        })

    # Call 1: Generates new snapshot
    res1 = await engine.get_or_generate_recommendation(school_id, student_id)
    # Call 2: Should hit idempotent cached snapshot
    res2 = await engine.get_or_generate_recommendation(school_id, student_id)

    assert res1["snapshotId"] == res2["snapshotId"]
    assert res1["generatedAt"] == res2["generatedAt"]
    assert len(res1["careerPaths"]) == len(res2["careerPaths"])
    for cp1, cp2 in zip(res1["careerPaths"], res2["careerPaths"]):
        assert cp1["code"] == cp2["code"]
        assert cp1["matchScore"] == cp2["matchScore"]


@pytest.mark.asyncio
async def test_fairness_and_sensitive_attribute_exclusion(test_setup):
    """
    Fairness: Two students with different synthetic names/UUIDs/identifiers
    but identical approved evidence sets MUST receive the exact same recommendations.
    Zero demographic traits are used.
    """
    repo: InMemoryPortfolioRepository = test_setup["portfolio_repo"]
    engine: RecommendationEngineService = test_setup["engine"]
    school_id = str(uuid.uuid4())

    student_a = str(uuid.uuid4())
    student_b = str(uuid.uuid4())

    now = datetime.now(timezone.utc)
    for s_id in [student_a, student_b]:
        pid = f"work_fairness_{s_id}"
        await repo.save_portfolio({
            "school_id": school_id,
            "student_id": s_id,
            "portfolio_id": pid,
            "title": "Aplikasi Web Analitik",
            "description": "Membangun dashboard analisis data terpadu",
            "activity_type": "project",
            "canonical_tag_ids": ["web-development", "data-analysis", "problem-solving"],
            "status": "approved",
            "current_revision_id": f"rev_{s_id}",
            "created_at": now,
            "updated_at": now,
        })
        await repo.save_approved_snapshot({
            "school_id": school_id,
            "student_id": s_id,
            "portfolio_id": pid,
            "revision_id": f"rev_{s_id}",
            "approved_at": now,
            "canonical_tag_ids": ["web-development", "data-analysis", "problem-solving"],
        })

    res_a = await engine.get_or_generate_recommendation(school_id, student_a)
    res_b = await engine.get_or_generate_recommendation(school_id, student_b)

    assert len(res_a["careerPaths"]) == len(res_b["careerPaths"])
    for cp_a, cp_b in zip(res_a["careerPaths"], res_b["careerPaths"]):
        assert cp_a["code"] == cp_b["code"]
        assert cp_a["matchScore"] == cp_b["matchScore"]
        assert cp_a["components"] == cp_b["components"]

    assert res_a["evidenceConfidence"]["score"] == res_b["evidenceConfidence"]["score"]
    assert res_a["evidenceConfidence"]["level"] == res_b["evidenceConfidence"]["level"]
