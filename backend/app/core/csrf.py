import hmac
import secrets

def generate_csrf_token() -> str:
    """Generate a high-entropy URL-safe CSRF token."""
    return secrets.token_urlsafe(32)

def validate_csrf_tokens(cookie_token: str | None, header_token: str | None) -> bool:
    """
    Validate CSRF using constant-time comparison between cookie and header tokens.
    Both must be present, non-empty, and identical.
    """
    if not cookie_token or not header_token:
        return False
    return hmac.compare_digest(cookie_token.strip(), header_token.strip())
