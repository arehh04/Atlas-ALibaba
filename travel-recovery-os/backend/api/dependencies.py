"""
dependencies.py - Authentication & Rate-Limiting Dependencies

Phase 4: Supports three auth modes (checked in order):
  1. Legacy static API key (SYNAPSE_API_SECRET)
  2. JWT Bearer token
  3. Managed API key (via APIKeyManager)

Also provides scope-checking and rate-limiting dependency factories.
"""

from backend.config import settings
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_429_TOO_MANY_REQUESTS,
)

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


# ---------------------------------------------------------------------------
# Auth Verification
# ---------------------------------------------------------------------------

async def verify_api_key(api_key: str | None = Security(api_key_header)) -> dict:
    """
    Verify incoming requests via a 3-step auth chain:
      1. Legacy static key match
      2. JWT decode
      3. Managed API key lookup
    Returns a dict with ``subject``, ``scopes``, and ``auth_mode``.
    """
    # In development/hackathon mode, allow local requests if no header passed unless REQUIRE_AUTH is explicitly set
    if api_key is None:
        if getattr(settings, "REQUIRE_AUTH", False) or settings.ENVIRONMENT == "production":
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing API key")
        return {"subject": "dev-user", "scopes": {"admin"}, "auth_mode": "dev"}

    # Strip "Bearer " prefix if present
    token = api_key
    token = token.removeprefix("Bearer ")

    # 1) Legacy static key
    if token and token == settings.SYNAPSE_API_SECRET and token != "default-insecure-secret-change-in-prod":
        return {"subject": "legacy-key", "scopes": {"admin"}, "auth_mode": "legacy"}

    # 2) JWT token
    try:
        from backend.auth.jwt_handler import _JOSE_AVAILABLE, verify_token
        if _JOSE_AVAILABLE:
            try:
                payload = verify_token(token)
                return {
                    "subject": payload.get("sub", "unknown"),
                    "scopes": set(payload.get("scopes", [])),
                    "auth_mode": "jwt",
                }
            except HTTPException:
                pass  # Fall through to managed keys
    except (ImportError, Exception):
        pass  # JWT module not available

    # 3) Managed API key
    try:
        from backend.auth.api_keys import get_api_key_manager
        manager = get_api_key_manager()
        key_info = manager.validate_key(api_key)  # accepts raw or "Bearer ..." form
        if key_info is not None:
            # validate_key returns an APIKey dataclass, not a dict
            return {
                "subject": key_info.name,
                "scopes": set(key_info.scopes),
                "auth_mode": "managed",
            }
    except (ImportError, Exception):
        pass  # Managed key module not available

    raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")


# ---------------------------------------------------------------------------
# Scope Checking
# ---------------------------------------------------------------------------

def verify_scope(required_scope: str):
    """Dependency factory: ensure the authenticated identity has *required_scope*."""

    async def _check(identity: dict = Depends(verify_api_key)) -> dict:
        if "admin" in identity["scopes"] or required_scope in identity["scopes"]:
            return identity
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f"Scope '{required_scope}' required",
        )

    return _check


# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------

async def rate_limit_dependency(request: Request, category: str = "default") -> None:
    """Async rate-limit check using Redis sorted-set sliding window."""
    from backend.auth.rate_limiter import get_rate_limiter

    limiter = get_rate_limiter()
    client_ip = request.client.host if request.client else "unknown"
    result = await limiter.check(client_ip, category)

    if not result.allowed:
        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "Retry-After": str(result.retry_after_seconds),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Limit": str(result.limit),
            },
        )


def rate_limit(category: str):
    """Dependency factory: apply per-category rate limiting."""

    async def _limit(request: Request) -> None:
        await rate_limit_dependency(request, category)

    return _limit
