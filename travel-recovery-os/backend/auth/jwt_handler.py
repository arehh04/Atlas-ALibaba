"""
jwt_handler.py - JWT Token Generation & Validation for SynapseAir

Secrets are resolved lazily from pydantic settings (backend/config.py), which
loads the profiled .env file — NOT from os.environ directly, since
pydantic-settings does not export .env values into the process environment.

Fail-closed: if only the public placeholder secret is configured, tokens can
neither be minted nor verified. A placeholder-signed token must never grant
access because the placeholder string is public knowledge (shipped in the repo).
"""
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    from jose import JWTError, jwt
    _JOSE_AVAILABLE = True
except ImportError:
    _JOSE_AVAILABLE = False
    JWTError = Exception

# Public placeholder — must never act as a signing/verification key.
_PLACEHOLDER_SECRET = "default-insecure-secret-change-in-prod"


def _get_secret_key() -> str:
    """Resolve the JWT signing secret from settings; refuse the placeholder."""
    from backend.config import settings
    secret = settings.JWT_SECRET_KEY or settings.SYNAPSE_API_SECRET
    if not secret or secret == _PLACEHOLDER_SECRET:
        raise RuntimeError(
            "JWT_SECRET_KEY (or SYNAPSE_API_SECRET) must be set to a real secret "
            "before issuing or validating JWTs — refusing to use the public placeholder."
        )
    return secret


def _get_algorithm() -> str:
    from backend.config import settings
    return settings.JWT_ALGORITHM


def _get_expire_minutes() -> int:
    from backend.config import settings
    return settings.JWT_EXPIRE_MINUTES


def create_access_token(subject: str, scopes=None, expires_delta=None, extra_claims=None) -> str:
    """Generate a JWT access token."""
    if not _JOSE_AVAILABLE:
        raise RuntimeError("python-jose is required: pip install python-jose[cryptography]")
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=_get_expire_minutes()))
    payload = {"sub": subject, "iat": now, "exp": expire, "type": "access"}
    if scopes:
        payload["scopes"] = scopes
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, _get_secret_key(), algorithm=_get_algorithm())


def verify_token(token: str, required_scope=None) -> dict[str, Any]:
    """Validate a JWT token and extract claims."""
    if not _JOSE_AVAILABLE:
        raise RuntimeError("python-jose is required.")
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[_get_algorithm()])
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")
    exp = payload.get("exp")
    if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
        raise ValueError("Token has expired")
    if required_scope:
        token_scopes = payload.get("scopes", [])
        if required_scope not in token_scopes and "admin" not in token_scopes:
            raise ValueError(f"Token lacks required scope: {required_scope}")
    return payload


def create_api_token(key_id: str, scopes: list, expires_days: int = 365) -> str:
    """Create a long-lived API token."""
    return create_access_token(subject=key_id, scopes=scopes, expires_delta=timedelta(days=expires_days),
                               extra_claims={"type": "api_key"})


def refresh_token(original_token: str) -> str:
    """Refresh an existing valid token with new expiry."""
    payload = verify_token(original_token)
    return create_access_token(subject=payload["sub"], scopes=payload.get("scopes"),
                               extra_claims={k: v for k, v in payload.items() if k not in ("sub", "iat", "exp", "scopes", "type")})
