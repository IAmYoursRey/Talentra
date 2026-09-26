from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .core.config import settings
from .core.database import engine
from .api.v1.auth import router as auth_router
from .api.v1.rbac_test import router as rbac_test_router
from .api.v1.health import router as health_router
from .api.v1.skill_tags import router as skill_tags_router
from .api.v1.student_portfolio import router as student_portfolio_router
from .api.v1.teacher_reviews import router as teacher_reviews_router
from .api.v1.student_skills import router as student_skills_router
from .api.v1.student_recommendations import router as student_recommendations_router
from .api.v1.admin_users import router as admin_users_router
from .api.v1.admin_classes import router as admin_classes_router
from .api.v1.admin_analytics import router as admin_analytics_router
from .api.v1.student_cv import router as student_cv_router
from .api.v1.admin_cv import router as admin_cv_router
from .api.v1.public_verify import router as public_verify_router
from .api.v1.storage import router as storage_router


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if "Referrer-Policy" not in response.headers:
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup lifecycle
    yield
    # Shutdown lifecycle
    try:
        await engine.dispose()
    except Exception:
        pass


def create_app() -> FastAPI:
    # Fail-fast check on startup if running in production
    if settings.app_env == "production":
        settings.validate_production_safety()

    app = FastAPI(
        title="TALENTRA.ID Platform Engine",
        version="0.3.0",
        description="Phase 3 Production Data Foundation Platform — PostgreSQL + MongoDB + Object Storage",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
        lifespan=lifespan,
    )

    # Security Headers
    app.add_middleware(SecurityHeadersMiddleware)

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )

    # Standardized Error Envelope Handlers
    from fastapi.responses import JSONResponse
    from fastapi.exceptions import RequestValidationError
    from fastapi import HTTPException
    import uuid

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.detail},
            )
        req_id = str(uuid.uuid4())
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": str(exc.detail),
                    "requestId": req_id,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        req_id = str(uuid.uuid4())
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Format data permintaan tidak valid.",
                    "requestId": req_id,
                }
            },
        )

    # Register Routers
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(rbac_test_router, prefix=settings.api_prefix)
    app.include_router(skill_tags_router, prefix=settings.api_prefix)
    app.include_router(student_portfolio_router, prefix=settings.api_prefix)
    app.include_router(teacher_reviews_router, prefix=settings.api_prefix)
    app.include_router(student_skills_router, prefix=settings.api_prefix)
    app.include_router(student_recommendations_router, prefix=settings.api_prefix)
    app.include_router(admin_users_router, prefix=settings.api_prefix)
    app.include_router(admin_classes_router, prefix=settings.api_prefix)
    app.include_router(admin_analytics_router, prefix=settings.api_prefix)
    app.include_router(student_cv_router, prefix=settings.api_prefix)
    app.include_router(admin_cv_router, prefix=settings.api_prefix)
    app.include_router(public_verify_router, prefix=settings.api_prefix)
    app.include_router(storage_router, prefix=settings.api_prefix)

    return app


app = create_app()
