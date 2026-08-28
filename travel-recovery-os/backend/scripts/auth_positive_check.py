"""Positive-path auth check: the REAL secret must work via all three auth modes."""
import asyncio
import sys

import httpx

BASE_URL = "http://127.0.0.1:8001"


def read_env_value(key: str) -> str:
    """Read a key from backend/.env, mirroring the server's pydantic resolution."""
    import os
    from pathlib import Path
    env = Path(__file__).resolve().parents[1] / ".env"
    values = {}
    for line in env.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    return values.get(key) or os.environ.get(key, "")


async def main():
    secret = read_env_value("SYNAPSE_API_SECRET")
    jwt_secret = read_env_value("JWT_SECRET_KEY") or secret
    if not secret:
        print("No secret found — aborting")
        return
    print("=" * 64)
    print("  POSITIVE-PATH CHECK — real secret via all auth modes")
    print("=" * 64)

    async with httpx.AsyncClient(timeout=15.0) as c:
        payload = {"pnr": "PNR-AUTH-OK"}

        # 1) Legacy static key (Bearer)
        r = await c.post(f"{BASE_URL}/webhook/disruption", json=payload,
                         headers={"Authorization": f"Bearer {secret}"})
        print(f"[1] Legacy static key (Bearer) : {'OK (200)' if r.status_code == 200 else f'FAIL ({r.status_code})'}")

        # 2) Managed API key (raw, no Bearer) — previously broken for ALL keys
        r = await c.post(f"{BASE_URL}/webhook/disruption", json=payload,
                         headers={"Authorization": secret})
        print(f"[2] Managed API key (raw)      : {'OK (200)' if r.status_code == 200 else f'FAIL ({r.status_code})'}")

        # 3) Properly-signed JWT with the real JWT secret
        try:
            from jose import jwt
            token = jwt.encode({"sub": "pos-check", "scopes": ["admin"], "type": "access"},
                               jwt_secret, algorithm="HS256")
            r = await c.post(f"{BASE_URL}/webhook/disruption", json=payload,
                             headers={"Authorization": f"Bearer {token}"})
            print(f"[3] JWT signed with real secret: {'OK (200)' if r.status_code == 200 else f'FAIL ({r.status_code})'}")
        except ImportError:
            print("[3] python-jose unavailable — skipped")


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
