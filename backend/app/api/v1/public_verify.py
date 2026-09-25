from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, Response, HTTPException, Depends

from ...core.rate_limiter import public_verify_rate_limiter
from ...services.public_verification_service import PublicVerificationService

router = APIRouter(prefix="/public/verify", tags=["Public CV Authenticity Verification"])

_public_verification_service: Optional[PublicVerificationService] = None


def get_public_verification_service() -> PublicVerificationService:
    global _public_verification_service
    if _public_verification_service is None:
        _public_verification_service = PublicVerificationService()
    return _public_verification_service


def set_public_verification_service(svc: Optional[PublicVerificationService]) -> None:
    global _public_verification_service
    _public_verification_service = svc


@router.get("/{token}")
async def verify_cv_token(
    token: str,
    request: Request,
    response: Response,
    service: PublicVerificationService = Depends(get_public_verification_service),
) -> Dict[str, Any]:
    """
    Public authenticity verification endpoint for recruiters, institutions, and the public.
    Resolves QR token to verified student credentials.
    Unauthenticated. Rate-limited. Stale-cache prevention enforced (no-store).
    """
    client_ip = request.client.host if request.client else "unknown"
    if public_verify_rate_limiter.is_rate_limited(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Batas permintaan verifikasi terlampaui. Silakan coba kembali beberapa saat lagi.",
        )
    public_verify_rate_limiter.record_request(client_ip)

    # Privacy and security headers
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"

    return await service.verify_public_token(token)
