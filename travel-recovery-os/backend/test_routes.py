import asyncio
import httpx
from datetime import datetime, timedelta

CLIENT_ID = "CTR12752_api_1"
CLIENT_SECRET = "sandbox-sk-CTR12752_api_1"
BASE_URL = "https://sandbox.atriptech.com"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Accept-Encoding": "gzip",
    "x-atlas-client-id": CLIENT_ID,
    "x-atlas-client-secret": CLIENT_SECRET,
}


async def check_route(origin, dest, trip_type="1", adult_num=1, child_num=0, infant_num=0, ret_date=None):
    date_str = (datetime.now() + timedelta(days=14)).strftime("%Y%m%d")
    body = {
        "cid": CLIENT_ID,
        "tripType": trip_type,
        "adultNum": adult_num,
        "childNum": child_num,
        "infantNum": infant_num,
        "fromCity": origin,
        "toCity": dest,
        "fromDate": date_str,
        "currency": "USD",
        "requestSource": "uat-check",
    }
    if ret_date:
        body["retDate"] = ret_date
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{BASE_URL}/search.do", json=body, headers=HEADERS)
        data = r.json()
        status = data.get("status")
        msg = data.get("msg")
        routings = data.get("routings", [])
        print(f"{origin}->{dest} (trip={trip_type}, adt={adult_num}, chd={child_num}): status={status}, count={len(routings)}")
        if routings:
            r0 = routings[0]
            print(f"   Routing 0: adultPrice={r0.get('adultPrice')}, adultTax={r0.get('adultTax')}, childPrice={r0.get('childPrice')}, childTax={r0.get('childTax')}, currency={r0.get('currency')}")
            # check ancillaries (baggage / seat / etc)
            if "ancillaries" in r0 or "baggages" in r0 or "seats" in r0:
                print(f"   Ancillaries keys: {[k for k in r0.keys() if 'bag' in k.lower() or 'seat' in k.lower() or 'anc' in k.lower()]}")
        else:
            print(f"   Msg: {msg}")


import pytest


@pytest.mark.asyncio
async def test_reference_routes():
    """Verify live/fallback routing for reference test route pairs."""
    await check_route("AMS", "MAA", "1", 1, 0)
    await check_route("COK", "DXB", "1", 1, 0)


async def main():
    print("Testing Reference Routes on Atlas Sandbox:")
    # 1. 6E AMS -> MAA
    await check_route("AMS", "MAA", "1", 1, 0)
    # 2. FA DUR -> CPT (Roundtrip, 2 adt + 1 chd)
    ret = (datetime.now() + timedelta(days=20)).strftime("%Y%m%d")
    await check_route("DUR", "CPT", "2", 2, 1, 0, ret)
    # 3. 7C PUS -> CJU
    await check_route("PUS", "CJU", "1", 1, 0)
    # 4. IX BOM -> IXR
    await check_route("BOM", "IXR", "1", 1, 0)
    # 5. 6E COK -> DXB
    await check_route("COK", "DXB", "1", 1, 0)
    # 6. SM ELQ -> HMB
    await check_route("ELQ", "HMB", "1", 1, 0)


if __name__ == "__main__":
    asyncio.run(main())

