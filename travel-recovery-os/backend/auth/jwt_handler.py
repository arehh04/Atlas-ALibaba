"""
jwt_handler.py - JWT Token Generation & Validation for SynapseAir
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

try:
    from jose import jwt, JWTError
    _JOSE_AVAILABLE = True
except ImportError:
    _JOSE_AVAILABLE = False
    JWTError = Exception

SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SYNAPSE_API_SECRET", "default-insecure-secret-change-in-prod"))
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


def create_access_token(subject: str, scopes=None, expires_delta=None, extra_claims=None) -> str:
    """Generate a JWT access token."""
    if not _JOSE_AVAILABLE:
        raise RuntimeError("python-jose is required: pip install python-jose[cryptography]")
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": subject, "iat": now, "exp": expire, "type": "access"}
    if scopes:
        payload["scopes"] = scopes
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str, required_scope=None) -> Dict[str, Any]:
    """Validate a JWT token and extract claims."""
    if not _JOSE_AVAILABLE:
        raise RuntimeError("python-jose is required.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
                               extra_claims={k: v for k, v in payload.items() if k not in ("sub","iat","exp","scopes","type")})
