import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Header, Query, Response, status, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...core.config import settings
from ...core.idempotency import idempotency_manager
from ...domain.enums import UserRole
from ...api.dependencies import require_role, AuthContext
from ...services.portfolio_service import (
    PortfolioService,
    CreatePortfolioDTO,
    UpdatePortfolioDTO,
    EvidenceInput,
)
from ...services.industry_translator import IndustryTranslatorService

router = APIRouter(prefix="/student/portfolio", tags=["Student Portfolio"])

_portfolio_service: Optional[PortfolioService] = None


def get_portfolio_service() -> PortfolioService:
    global _portfolio_service
    if _portfolio_service is None:
        _portfolio_service = PortfolioService()
    return _portfolio_service


def set_portfolio_service(svc: Optional[PortfolioService]) -> None:
    global _portfolio_service
    _portfolio_service = svc


class UploadIntentRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    contentType: str
    sizeBytes: int = Field(gt=0)
    checksum: Optional[str] = None


class PortfolioListResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_portfolio_draft(
    payload: CreatePortfolioDTO,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Creates a new portfolio item and version 1 revision in draft status.
    Authoritative student_id and school_id are bound strictly from authenticated session.
    """
    operation = "create_portfolio"
    if idempotency_key:
        cached = await idempotency_manager.get_cached_response(
            auth_ctx.user_id, operation, idempotency_key
        )
        if cached:
            cached_code, cached_body = cached
            return JSONResponse(status_code=cached_code, content=cached_body)

    result = await service.create_draft(
        school_id=auth_ctx.school_id,
        student_id=auth_ctx.user_id,
        payload=payload,
    )

    if idempotency_key:
        await idempotency_manager.store_response(
            auth_ctx.user_id, operation, idempotency_key, status.HTTP_201_CREATED, result
        )

    return result


@router.get("", response_model=PortfolioListResponse)
async def list_student_portfolios(
    status_filter: Optional[str] = Query(None, alias="status"),
    tag: Optional[str] = Query(None),
    activity_type: Optional[str] = Query(None, alias="activityType"),
    search: Optional[str] = Query(None),
    sort_by: str = Query("newest", alias="sortBy"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Lists portfolios owned by the authenticated student.
    Enforces tenant and student isolation — cannot query another student's work.
    """
    items, total = await service.list_portfolios(
        school_id=auth_ctx.school_id,
        student_id=auth_ctx.user_id,
        status_filter=status_filter,
        tag=tag,
        activity_type=activity_type,
        search=search,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )
    return PortfolioListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{portfolio_id}")
async def get_portfolio_detail(
    portfolio_id: str,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Retrieves full detail of a portfolio owned by the student.
    Returns 404 if not found or cross-tenant/cross-user to prevent enumeration.
    """
    return await service.get_portfolio(
        school_id=auth_ctx.school_id,
        student_id=auth_ctx.user_id,
        portfolio_id=portfolio_id,
    )


@router.patch("/{portfolio_id}")
async def update_portfolio_draft(
    portfolio_id: str,
    payload: UpdatePortfolioDTO,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Updates an editable draft portfolio. Fails if status is not 'draft'.
    """
    return await service.update_draft(
        school_id=auth_ctx.school_id,
        student_id=auth_ctx.user_id,
        portfolio_id=portfolio_id,
        payload=payload,
    )


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_draft(
    portfolio_id: str,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Deletes an unsubmitted draft portfolio. Submitted items cannot be deleted by student.
    """
    deleted = await service.delete_draft(
        school_id=auth_ctx.school_id,
        student_id=auth_ctx.user_id,
        portfolio_id=portfolio_id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PORTFOLIO_NOT_FOUND",
                "message": "Karya draf tidak ditemukan untuk dihapus.",
            },
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{portfolio_id}/uploads", status_code=status.HTTP_201_CREATED)
async def request_upload_intent(
    portfolio_id: str,
    payload: UploadIntentRequest,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Registers an upload intent, validates declared size and mime policy, creates
    a pending storage_objects row in PostgreSQL, and generates a short-lived presigned upload URL.
    """
    operation = f"upload_intent:{portfolio_id}"
    if idempotency_key:
        cached = await idempotency_manager.get_cached_response(
            auth_ctx.user_id, operation, idempotency_key
        )
        if cached:
            cached_code, cached_body = cached
            return JSONResponse(status_code=cached_code, content=cached_body)

    result = await service.request_upload_intent(
        school_id=auth_ctx.school_id,
        student_id=auth_ctx.user_id,
        portfolio_id=portfolio_id,
        filename=payload.filename,
        content_type=payload.contentType,
        declared_size_bytes=payload.sizeBytes,
        checksum=payload.checksum,
    )

    if idempotency_key:
        await idempotency_manager.store_response(
            auth_ctx.user_id, operation, idempotency_key, status.HTTP_201_CREATED, result
        )

    return result


@router.post("/{portfolio_id}/uploads/{storage_object_id}/complete")
async def complete_upload(
    portfolio_id: str,
    storage_object_id: str,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Post-upload verification:
    Validates actual binary signature (magic bytes) to defeat MIME spoofing,
    runs security scanner hook, transitions status to 'available'.
    """
    operation = f"upload_complete:{storage_object_id}"
    if idempotency_key:
        cached = await idempotency_manager.get_cached_response(
            auth_ctx.user_id, operation, idempotency_key
        )
        if cached:
            cached_code, cached_body = cached
            return JSONResponse(status_code=cached_code, content=cached_body)

    result = await service.complete_upload(
        school_id=auth_ctx.school_id,
        student_id=auth_ctx.user_id,
        portfolio_id=portfolio_id,
        storage_object_id=storage_object_id,
    )

    if idempotency_key:
        await idempotency_manager.store_response(
            auth_ctx.user_id, operation, idempotency_key, status.HTTP_200_OK, result
        )

    return result


@router.get("/{portfolio_id}/evidence/{storage_object_id}/access")
async def get_evidence_download_access(
    portfolio_id: str,
    storage_object_id: str,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Issues short-lived download URL for authorized student to preview own uploaded evidence.
    URL is never permanently stored or cached by PWA.
    """
    # Enforce private, non-cacheable headers for sensitive asset URLs
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"

    return await service.get_evidence_download_access(
        school_id=auth_ctx.school_id,
        student_id=auth_ctx.user_id,
        portfolio_id=portfolio_id,
        storage_object_id=storage_object_id,
    )


@router.post("/{portfolio_id}/submit")
async def submit_portfolio(
    portfolio_id: str,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Authoritative submission gate:
    1. Enforces 3 to 5 active canonical skill tags
    2. Enforces at least 1 verified evidence item
    3. Atomically transitions draft -> submitted
    4. Locks revision snapshot as immutable submitted history
    5. Emits durable outbox event and audit log
    """
    operation = f"submit_portfolio:{portfolio_id}"
    if idempotency_key:
        cached = await idempotency_manager.get_cached_response(
            auth_ctx.user_id, operation, idempotency_key
        )
        if cached:
            cached_code, cached_body = cached
            return JSONResponse(status_code=cached_code, content=cached_body)

    result = await service.submit_portfolio(
        school_id=auth_ctx.school_id,
        student_id=auth_ctx.user_id,
        portfolio_id=portfolio_id,
    )

    if idempotency_key:
        await idempotency_manager.store_response(
            auth_ctx.user_id, operation, idempotency_key, status.HTTP_200_OK, result
        )

    return result


@router.post("/{portfolio_id}/revision")
async def begin_portfolio_revision(
    portfolio_id: str,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Initiates next revision cycle when status is 'revision_requested'.
    Previous submitted revision remains immutable; creates version N+1.
    """
    return await service.begin_revision(
        school_id=auth_ctx.school_id,
        student_id=auth_ctx.user_id,
        portfolio_id=portfolio_id,
    )


_translator_service: Optional[IndustryTranslatorService] = None


def get_translator_service() -> IndustryTranslatorService:
    global _translator_service
    if _translator_service is None:
        _translator_service = IndustryTranslatorService()
    return _translator_service


def set_translator_service(svc: Optional[IndustryTranslatorService]) -> None:
    global _translator_service
    _translator_service = svc


@router.post("/{portfolio_id}/professional-description")
async def generate_professional_description(
    portfolio_id: str,
    response: Response,
    force_regenerate: bool = Query(False),
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: IndustryTranslatorService = Depends(get_translator_service),
) -> Dict[str, Any]:
    """
    Translates raw student portfolio activity description into professional CV language.
    Strictly grounded in approved evidence. Denies draft, submitted, revision_requested, and rejected works.
    Never alters immutable portfolio revisions; saves as a derived professional snapshot.
    """
    response.headers["Cache-Control"] = "private, no-store"
    try:
        return await service.get_or_create_professional_description(
            school_id=auth_ctx.school_id,
            student_id=auth_ctx.user_id,
            portfolio_id=portfolio_id,
            force_regenerate=force_regenerate,
        )
    except ValueError as e:
        err_msg = str(e)
        if "not found or access denied" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PORTFOLIO_NOT_FOUND", "message": err_msg},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "TRANSLATION_REJECTED", "message": err_msg},
        )


@router.get("/{portfolio_id}/professional-description")
async def get_professional_description(
    portfolio_id: str,
    response: Response,
    auth_ctx: AuthContext = Depends(require_role(UserRole.STUDENT)),
    service: IndustryTranslatorService = Depends(get_translator_service),
) -> Dict[str, Any]:
    """
    Fetches the existing derived professional description for an approved portfolio.
    """
    response.headers["Cache-Control"] = "private, no-store"
    try:
        return await service.get_or_create_professional_description(
            school_id=auth_ctx.school_id,
            student_id=auth_ctx.user_id,
            portfolio_id=portfolio_id,
            force_regenerate=False,
        )
    except ValueError as e:
        err_msg = str(e)
        if "not found or access denied" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PORTFOLIO_NOT_FOUND", "message": err_msg},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "TRANSLATION_REJECTED", "message": err_msg},
        )

