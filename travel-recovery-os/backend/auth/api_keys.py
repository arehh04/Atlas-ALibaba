"""
api_keys.py - API Key Management with Scopes for SynapseAir
"""
import hashlib, secrets, time, os
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Set


@dataclass
class APIKey:
    key_id: str
    key_hash: str
    name: str
    scopes: Set[str]
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    last_used_at: Optional[float] = None
    is_active: bool = True

    def is_expired(self):
        return False if self.expires_at is None else time.time() > self.expires_at

    def has_scope(self, required_scope):
        return "admin" in self.scopes or required_scope in self.scopes

    def to_dict(self):
        return {"key_id": self.key_id, "name": self.name, "scopes": list(self.scopes),
                "created_at": self.created_at, "expires_at": self.expires_at,
                "last_used_at": self.last_used_at, "is_active": self.is_active}


class APIKeyManager:
    """Manages API keys with scope-based authorization."""

    VALID_SCOPES = {"admin", "read-only", "webhook-only", "history", "stream"}

    def __init__(self):
        self._keys_by_hash: Dict[str, APIKey] = {}
        self._keys_by_id: Dict[str, APIKey] = {}
        self._register_default_key()

    def _register_default_key(self):
        default_secret = os.getenv("SYNAPSE_API_SECRET", "default-insecure-secret-change-in-prod")
        self._register_raw_key(raw_key=default_secret, key_id="default",
                               name="Default API Key (from env)", scopes={"admin"})

    def _register_raw_key(self, raw_key, key_id, name, scopes):
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = APIKey(key_id=key_id, key_hash=key_hash, name=name, scopes=scopes)
        self._keys_by_hash[key_hash] = api_key
        self._keys_by_id[key_id] = api_key
        return api_key

    def create_key(self, name, scopes=None, expires_days=None):
        """Generate a new API key. Returns (raw_key_string, APIKey info dict)."""
        raw_key = f"sk-{secrets.token_urlsafe(32)}"
        key_id = secrets.token_hex(8)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = APIKey(key_id=key_id, key_hash=key_hash, name=name, scopes=scopes or {"read-only"},
                         expires_at=time.time() + (expires_days * 86400) if expires_days else None)
        self._keys_by_hash[key_hash] = api_key
        self._keys_by_id[key_id] = api_key
        return raw_key, api_key.to_dict()

    def validate_key(self, raw_key):
        if raw_key.startswith("Bearer "):
            raw_key = raw_key[7:]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = self._keys_by_hash.get(key_hash)
        if api_key is None or not api_key.is_active or api_key.is_expired():
            return None
        api_key.last_used_at = time.time()
        return api_key

    def revoke_key(self, key_id):
        api_key = self._keys_by_id.get(key_id)
        if api_key:
            api_key.is_active = False
            return True
        return False

    def list_keys(self):
        return [k.to_dict() for k in self._keys_by_id.values()]

    def get_key(self, key_id):
        api_key = self._keys_by_id.get(key_id)
        return api_key.to_dict() if api_key else None


_global_manager = None


def get_api_key_manager() -> APIKeyManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = APIKeyManager()
    return _global_manager
