import os
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse, Response as RawResponse, RedirectResponse
from pydantic import BaseModel, Field

from ...core.config import settings
from ...repositories.upload_intent import BlobUploadIntentRepository
from ...storage import get_object_storage
from ...storage.local import LocalObjectStorage
from ...storage.vercel_blob import VercelBlobStorage

router = APIRouter(prefix="/storage", tags=["Storage"])


class VerifyIntentRequest(BaseModel):
    token: str = Field(min_length=1)
    pathname: Optional[str] = None


@router.post("/verify-intent")
async def verify_upload_intent(payload: VerifyIntentRequest):
    """
    Verifies short-lived direct upload authorization intent against Neon PostgreSQL.
    Used by Vercel Blob client upload route handler to prevent unauthorized uploads.
    """
    repo = BlobUploadIntentRepository()
    intent = await repo.get_valid_intent(payload.token)
    if not intent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_UPLOAD_INTENT", "message": "Otorisasi unggahan tidak valid atau telah kedaluwarsa."},
        )

    if payload.pathname and intent.pathname != payload.pathname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PATHNAME_MISMATCH", "message": "Jalur penyimpanan tidak sesuai dengan otorisasi unggahan."},
        )

    return {
        "valid": True,
        "intentId": intent.id,
        "pathname": intent.pathname,
        "maxBytes": intent.max_bytes,
        "contentType": intent.expected_content_type,
        "portfolioId": intent.portfolio_id,
        "studentId": intent.student_id,
        "schoolId": intent.school_id,
    }


@router.put("/upload")
async def local_upload_endpoint(
    request: Request,
    key: str = Query(...),
    expires: int = Query(...),
    sig: str = Query(...),
):
    """
    Local development upload handler simulating presigned cloud PUT.
    """
    storage = get_object_storage()
    if not isinstance(storage, LocalObjectStorage):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Direct PUT upload endpoint is only supported in local development storage mode.",
        )

    if not storage.verify_signed_url("upload", key, expires, sig):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tautan unggah tidak valid atau telah kedaluwarsa.",
        )

    body = await request.body()
    content_type = request.headers.get("content-type", "application/octet-stream")
    storage.write_object(key, body, content_type)
    return {"status": "success", "size": len(body), "key": key}


@router.get("/download")
async def storage_download_endpoint(
    key: str = Query(...),
    expires: int = Query(...),
    sig: str = Query(...),
):
    """
    Secure download access endpoint validating short-lived signature.
    """
    storage = get_object_storage()

    if isinstance(storage, LocalObjectStorage):
        if not storage.verify_signed_url("download", key, expires, sig):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tautan unduh tidak valid atau telah kedaluwarsa.",
            )
        try:
            full_path = storage._get_full_path(key)
            if not os.path.exists(full_path):
                raise HTTPException(status_code=404, detail="Berkas tidak ditemukan.")
            return FileResponse(
                path=full_path,
                headers={
                    "Cache-Control": "no-store, no-cache, must-revalidate, private",
                    "Pragma": "no-cache",
                },
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid path.")

    elif isinstance(storage, VercelBlobStorage):
        if not storage.verify_signed_url("blob_download", key, expires, sig):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tautan unduh tidak valid atau telah kedaluwarsa.",
            )
        try:
            data = storage.get_object_bytes(key)
            head = storage.head_object(key)
            content_type = (head or {}).get("content_type", "application/octet-stream")
            return RawResponse(
                content=data,
                media_type=content_type,
                headers={
                    "Cache-Control": "no-store, no-cache, must-revalidate, private",
                    "Pragma": "no-cache",
                },
            )
        except Exception:
            raise HTTPException(status_code=404, detail="Berkas tidak ditemukan di penyimpanan blob.")

    raise HTTPException(status_code=400, detail="Unsupported storage provider for direct download.")
