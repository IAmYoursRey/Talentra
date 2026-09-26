import sys
from pathlib import Path

# Deterministically configure Python import paths for Vercel Serverless Function runtime
_CURRENT_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _CURRENT_DIR.parent
_BACKEND_DIR = _ROOT_DIR / "backend"

if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

# Import the authoritative FastAPI application instance
from app.main import app  # noqa: E402

__all__ = ["app"]
