import asyncio
import os
import sys
import httpx
from datetime import datetime, timedelta

# Ensure parent directory is in sys.path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import settings


async def run_smoke_test():
    print(f"\n{'='*70}")
    print(f"ATLAS PRODUCTION GO-LIVE SMOKE TEST")
    print(f"{'='*70}")

    search_url = (getattr(settings, "ATLAS_SEARCH_BASE_URL", None) or getattr(settings, "ATLAS_BASE_URL", "https://sandbox.atriptech.com")).rstrip("/")
    tx_url = (getattr(settings, "ATLAS_TRANSACTION_BASE_URL", None) or getattr(settings, "ATLAS_BASE_URL", "https://sandbox.atriptech.com")).rstrip("/")
    client_id = getattr(settings, "ATLAS_CLIENT_ID", "")
    client_secret = getattr(settings, "ATLAS_CLIENT_SECRET", "")
    env_mode = getattr(settings, "ATLAS_ENV", "sandbox")

    print(f"Environment Mode        : {env_mode.upper()}")
    print(f"Search Base URL         : {search_url}")
    print(f"Transaction Base URL    : {tx_url}")
    print(f"Client ID               : {client_id}")
    print(f"Client Secret Masked    : {client_secret[:6]}...{client_secret[-4:] if len(client_secret) > 10 else '***'}")
    print(f"{'='*70}\n")

    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Encoding": "gzip",
        "x-atlas-client-id": client_id,
        "x-atlas-client-secret": client_secret,
    }

    # 1. Non-destructive Search Smoke Test
    test_date = (datetime.now() + timedelta(days=21)).strftime("%Y%m%d")
    print(f"1. Testing Search Endpoint ({search_url}/search.do)...")
    search_payload = {
        "cid": client_id,
        "tripType": "1",
        "adultNum": 1,
        "childNum": 0,
        "infantNum": 0,
        "fromCity": "KUL",
        "toCity": "HGH",
        "fromDate": test_date,
        "currency": "USD",
        "requestSource": "production-smoke-test",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            r = await client.post(f"{search_url}/search.do", json=search_payload, headers=headers)
            print(f"   HTTP Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                status = data.get("status")
                msg = data.get("msg")
                routings = data.get("routings", [])
                if status == 0:
                    print(f"   [OK] Search connection passed! Found {len(routings)} routings.")
                else:
                    print(f"   [WARN] API returned status {status}: {msg}")
            else:
                print(f"   [FAIL] HTTP returned {r.status_code}: {r.text[:200]}")
        except Exception as exc:
            print(f"   [ERROR] Connection failed: {exc}")

    # 2. Transaction Gateway Reachability Test
    print(f"\n2. Testing Transaction Gateway Reachability ({tx_url})...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Check gateway response on verify with invalid routing (should return business status 102/103 instead of 404/502)
            r = await client.post(
                f"{tx_url}/verify.do",
                json={"cid": client_id, "routingIdentifier": "SMOKE_TEST_CHECK", "requestSource": "production-smoke-test"},
                headers=headers
            )
            print(f"   HTTP Status: {r.status_code}")
            if r.status_code == 200:
                print(f"   [OK] Transaction gateway reachable and authenticated.")
            else:
                print(f"   [WARN] Gateway responded with HTTP {r.status_code}")
        except Exception as exc:
            print(f"   [ERROR] Gateway unreachable: {exc}")

    print(f"\n{'='*70}")
    print("SMOKE TEST SEQUENCE COMPLETE")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(run_smoke_test())

