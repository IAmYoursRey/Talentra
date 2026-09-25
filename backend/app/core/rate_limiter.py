import hashlib
import time
from collections import defaultdict

class LoginRateLimiter:
    """
    In-memory rate limiter that tracks login attempts by hashed identifier
    to avoid exposing or storing raw national identifiers.
    """
    def __init__(self, max_attempts: int = 5, window_seconds: int = 60, pepper: str = "talentra-rate-pepper-v1"):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.pepper = pepper
        # key -> list of attempt timestamps
        self.attempts: dict[str, list[float]] = defaultdict(list)

    def _hash_key(self, identifier: str) -> str:
        salted = f"{identifier}:{self.pepper}".encode("utf-8")
        return hashlib.sha256(salted).hexdigest()

    def is_rate_limited(self, identifier: str) -> bool:
        key = self._hash_key(identifier)
        now = time.time()
        # Clean older timestamps
        cutoff = now - self.window_seconds
        self.attempts[key] = [t for t in self.attempts[key] if t > cutoff]
        return len(self.attempts[key]) >= self.max_attempts

    def record_attempt(self, identifier: str) -> None:
        key = self._hash_key(identifier)
        self.attempts[key].append(time.time())

    def reset(self, identifier: str) -> None:
        key = self._hash_key(identifier)
        if key in self.attempts:
            del self.attempts[key]

login_rate_limiter = LoginRateLimiter()


class PublicVerifyRateLimiter:
    """
    In-memory rate limiter for public verification endpoint keyed by hashed client IP
    to protect against enumeration and brute force without storing raw IP addresses.
    """
    def __init__(self, max_requests: int = 60, window_seconds: int = 60, pepper: str = "talentra-public-verify-pepper-v1"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.pepper = pepper
        self.requests: dict[str, list[float]] = defaultdict(list)

    def _hash_client(self, client_ip: str) -> str:
        salted = f"{client_ip}:{self.pepper}".encode("utf-8")
        return hashlib.sha256(salted).hexdigest()

    def is_rate_limited(self, client_ip: str) -> bool:
        key = self._hash_client(client_ip)
        now = time.time()
        cutoff = now - self.window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]
        return len(self.requests[key]) >= self.max_requests

    def record_request(self, client_ip: str) -> None:
        key = self._hash_client(client_ip)
        self.requests[key].append(time.time())

    def reset(self, client_ip: str) -> None:
        key = self._hash_client(client_ip)
        if key in self.requests:
            del self.requests[key]


public_verify_rate_limiter = PublicVerifyRateLimiter(max_requests=60)
