---
name: "atlas-api-integration-advisor"
description: "Assists clients integrating with Atlas flight booking API. Provides flow recommendations, code generation (Python/PHP/Java/Node.js), endpoint guidance, and step-by-step onboarding support. Invoke when a client needs help understanding or implementing their Atlas API integration. Triggers: 集成Atlas, Atlas API对接, 机票预订接入, booking API, flight API integration, 配置沙箱, 生成代码, 错误码诊断, sandbox testing, go-live onboarding."
---

# Atlas API Integration Advisor

This skill helps **clients (customers)** who are integrating with the Atlas flight booking platform. It provides architectural guidance, flow selection, code examples, and step-by-step onboarding support — from understanding the available booking flows to production go-live.

---

## 1. How This Skill Works

```
Client Question
      │
      ▼
┌─────────────────────────────────┐
│  1. Identify Client Scenario    │
│     (OTA / TMC / Price Compare  │
│      / Direct Booker)           │
└──────────┬──────────────────────┘
           ▼
┌─────────────────────────────────┐
│  2. Recommend Booking Flow      │
│     (Search→Verify→Order→Pay    │
│      or GetOffer→Order→Pay)     │
└──────────┬──────────────────────┘
           ▼
┌─────────────────────────────────┐
│  3. Generate Integration Code   │
│     (in client's language)      │
└──────────┬──────────────────────┘
           ▼
┌─────────────────────────────────┐
│  4. Provide Onboarding Steps    │
│     (Credential → Sandbox       │
│      → UAT → Production)        │
└──────────┬──────────────────────┘
           ▼
┌─────────────────────────────────┐
│  5. Troubleshoot Issues         │
│     (via MCP doc lookups)       │
└─────────────────────────────────┘
```

**When more precise API field/schema info is needed, use the MCP service** (`resources.atriptech.com/~gitbook/mcp`) to look up the latest API documentation. The MCP service provides exact endpoint definitions, request/response schemas, and error code explanations.

---

## 2. Booking Flows Overview

Atlas provides two booking flows. The choice depends on the client's business model:

### Flow A: Search → Verify → Order → Pay (Standard Booking Flow)

```
search.do ──→ verify.do ──┬── [getLuggage.do] ──┐
                          │        │             │
                          │  └─ baggage product  │
                          │        codes         │
                          ├── [seatAvailability]─┤
                          │        │             │
                          │  └─ seat product     │
                          │        codes         │
                          │                      │
                          └────────┬─────────────┘
                                   ▼
                             order.do ──→ [orderCommit.do (FR only)] ──→ pay.do
                                   │
                              orderNo + pnrCode
```

| Step | Endpoint | Purpose | Key Output |
|------|----------|---------|------------|
| 1 | `search.do` | Search flights by route + date | `routingIdentifier`, `fromSegments` |
| 2 | `verify.do` | Verify price, get session | `sessionId` (valid for 2 hours) |
| 3a | `getLuggage.do` (optional) | Query baggage options | `productCode` for each bag option |
| 3b | `seatAvailability.do` (optional) | Query seat map & pricing | `productCode` for selected seat |
| 4 | `order.do` | Create booking | `orderNo`, `pnrCode` |
| - | `orderCommit.do` | **FR only**: Commit order before pay | confirmation |
| 5 | `pay.do` | Complete payment | `status: 0` |
| 6 | `queryOrderDetails.do` | Check order/ticket status | `orderStatus`, `ticketStatus` |

**Best for:** Most clients who use Atlas as their primary flight shopping/booking source.

### Flow B: Get Offer → Order → Pay (Get Offer Booking Flow)

```
getOffers.do ──┬── [getLuggage.do] ──┐
               │        │             │
               │  └─ baggage product  │
               │        codes         │
               ├── [seatAvailability]─┤
               │        │             │
               │  └─ seat product     │
               │        codes         │
               │                      │
               └────────┬─────────────┘
                        ▼
                  order.do ──→ [orderCommit.do (FR only)] ──→ pay.do
```

| Step | Endpoint | Purpose | Key Output |
|------|----------|---------|------------|
| 1 | `getOffers.do` | Get price quote for known itinerary | `offerId` |
| 2a | `getLuggage.do` (optional) | Query baggage options | `productCode` |
| 2b | `seatAvailability.do` (optional) | Query seat map | `productCode` |
| 3 | `order.do` | Create booking (using `offerId`) | `orderNo`, `pnrCode` |
| 4 | `pay.do` | Complete payment | `status: 0` |

**Best for:** Clients who already know the target itinerary (e.g., own shopping results) or need an independent real-time price check without relying on Atlas as the primary search source.

### ❌ Price Compare Search — NOT a Booking Flow

```
priceCompareSearch.do
```

**`priceCompareSearch.do` is NOT part of any booking flow.** It is exclusively for:
- **Pre-sale route coverage checks**
- **Raw price discovery / fare comparison** (e.g., by flight deck/travel bloggers)
- **Low-traffic scenario price validation**

> ⚠️ **Critical:** Do NOT use `priceCompareSearch.do` as a production booking price source.
> - Only available to pre-sale customers
> - Default quota: 1,000 calls/day
> - The returned price is NOT suitable for production booking

---

## 3. Decision Tree: Which Flow Does the Client Need?

```
Does the client use Atlas as their primary flight shopping source?
│
├── YES → Recommend Flow A (Search → Verify → Order → Pay)
│         └── The client calls search.do to display flights to their end users
│
├── NO — Does the client already have their own flight data/shopping results?
│   │
│   ├── YES → Recommend Flow B (GetOffer → Order → Pay)
│   │         └── The client calls getOffers.do to get a price quote
│   │             for a known itinerary, then proceeds to booking
│   │
│   └── NO — Is the client doing pre-sale fare comparison only?
│       │
│       ├── YES → Use priceCompareSearch.do (NOT a booking flow)
│       │         └── Only for price discovery, not ticketing
│       │
│       └── NO → Recommend Flow A as default
│
├── HYBRID — Does the client have multiple business lines?
│   │         (e.g., an OTA that has self-shopped results for some routes
│   │          and uses Atlas search for others)
│   │
│   ├── YES → Implement BOTH Flow A + Flow B
│   │         ├── Use Flow A for routes where Atlas provides shopping
│   │         ├── Use Flow B for routes with pre-known itineraries
│   │         └── Build a routing table to decide which flow to use
│   │             per route/partner
│   │
│   └── NO → (already covered by branches above)
│
└── [FR specific]: Flow A + orderCommit.do between order and pay
```

> 🔴 **CHECKPOINT · Confirm Flow Selection**
> Present the recommended flow (Flow A / Flow B / Price Compare Only / Hybrid) to the client and confirm before proceeding to implementation.
> If the client is unsure, return to the decision tree and re-evaluate.

---

## 4. Getting Started: Onboarding Steps

### Step 1: Obtain Sandbox Credentials

Before you can use the API, you need an ATRIP account and sandbox credentials. Contact your Atlas account manager or register through the Atlas partner portal to get access.

```
ATRIP Portal → Profile → My Profile → Company Information → Generate
```

This generates a pair of **sandbox credentials** (valid only on sandbox URLs):
- **AK (Access Key)** = Client ID (`x-atlas-client-id`)
- **SK (Secret Key)** = Client Secret (`x-atlas-client-secret`)

**Important:** These are sandbox-only credentials. They will NOT work on production URLs. You will generate separate production credentials after go-live (see Step 3).

Sandbox base URL: `https://sandbox.atriptech.com`

### Step 2: Test in Sandbox

1. Choose a supported test route (see `references/integration-scenarios.md`)
2. Implement the chosen flow
3. Verify end-to-end: search → verify → order → pay
4. Test ancillary flows (luggage, seat selection) if applicable
5. Test void and refund flows if applicable

### Step 3: Create Production Credentials

After UAT passes, the client manager changes the account to LIVE status. Once LIVE, return to ATRIP to generate **new production credentials** — these are different from your sandbox credentials.

```
ATRIP Portal → Profile → My Profile → Company Information → Generate (same path as sandbox)
```

**Credentials vs Environment:**

| Environment | Credentials | Base URL(s) |
|:-----------|:------------|:------------|
| Sandbox | AK/SK generated while account is in trial/uat status | `https://sandbox.atriptech.com` (single URL for all APIs) |
| Production | **New AK/SK** generated after account is LIVE | Two URLs: search + transaction (see below) |

> ⚠️ **Never use sandbox credentials on production URLs, or production credentials on sandbox URLs.** The credentials and URLs are bound to their respective environments. Using the wrong combination will result in authentication failures.

Production base URLs are shown in **ATRIP → Profile → My Profile → Company Information**. Production uses **separate** base URLs — **search and transaction APIs are on different domains, not just different paths. This is a critical configuration requirement.**

> 💡 **Production URLs (verify with ATRIP Portal → Profile → My Profile → Company Information):**
>
> **For China clients:**
> - Search: `https://search.yutu-api.com`
> - Transaction (verify, order, pay, ancillary, post-booking, refund, void, webhook): `https://api.yutu-api.com`
>
> **For International clients:**
> - Search: `https://api.atriptech.com/search`
> - Transaction (verify, order, pay, ancillary, post-booking, refund, void, webhook): `https://api.atriptech.com`
>
> ⚠️ **Replace `https://sandbox.atriptech.com` with these production URLs when going live. Never use the same base URL for search and transaction APIs in production.**

> 🔴 **CHECKPOINT · Confirm UAT Completion**
> Ensure all sandbox tests pass before requesting production credentials.
> Confirm with the client: Has the end-to-end flow been fully validated in sandbox? Are common error status codes covered?

### Step 4: Go Live

- [ ] Production credentials obtained
- [ ] Sandbox end-to-end testing completed
- [ ] Error handling implemented (common status codes)
- [ ] Post-booking flows tested (void, refund, ancillary)
- [ ] Webhook integration verified (if applicable)

---

## 5. How to Use MCP for Precise Documentation

When the client asks about specific API fields, error codes, or schema details, try the MCP service first:

```
MCP Endpoint: https://resources.atriptech.com/~gitbook/mcp
```

**Capabilities (if MCP is configured):**
- `searchDocumentation` — Search documentation by keyword
- `getPage` — Get full content of a specific doc page

**When to trigger MCP lookups:**
- Client asks about a specific response field (e.g., "what does refundStatus=T mean?")
- Client encounters an error code and wants the definition
- Client needs the full request/response schema for an endpoint
- Client wants to verify update notes or changelog entries

### MCP Not Available — Fallback Strategy

If `run_mcp` fails (MCP service not configured or unavailable), do not silently skip. Follow this fallback path:

```
Attempt MCP call (searchDocumentation / getPage)
     │
     ├── Success → Return precise documentation
     │
     └── Failed (MCP not configured) → Fallback to WebFetch
            │
            ├── Success → Parse content from docs site
            │
            └── Failed → Fallback to Skill built-in knowledge
                    │
                    └── Inform the client:
                        "MCP service is not currently configured.
                         Answer provided using built-in knowledge.
                         For the latest precise documentation,
                         install the Atlas MCP:
                         npx @anthropic-ai/claude-code mcp add atlas-docs \
                           --type url \
                           --url https://resources.atriptech.com/~gitbook/mcp"
```

**WebFetch alternatives when MCP is unavailable:**

```markdown
# When MCP is unavailable, use WebFetch to access the docs site directly
# Docs homepage: https://resources.atriptech.com/
# Search endpoint: https://resources.atriptech.com/?ask=<specific_question>

# Example: look up refundStatus field definition
WebFetch("https://resources.atriptech.com/?ask=What+does+refundStatus+mean")

# Example: look up specific endpoint schema
WebFetch("https://resources.atriptech.com/popular-topics/notification/notification-subscription")
```

> **Note:** MCP provides exact API reference data. This skill provides the integration guidance and context — use MCP for precision, use this skill for process/comprehension.  
> **If MCP is not configured, the built-in status code table (§7), request body examples (§8b), and error code tables already cover 80%+ of common questions — sufficient for standard integration scenarios.**

---

## 6. Authentication

All API calls require:

| Header | Description | Required For |
|--------|-------------|:------------:|
| `x-atlas-client-id` | API Access Key (AK) | All endpoints |
| `x-atlas-client-secret` | API Secret Key (SK) | All endpoints |
| `Content-Type` | `application/json` | All endpoints |
| `Accept-Encoding` | `gzip` | **Required** for `search.do` |
| `Accept` | `application/json` | All endpoints |

Without `Accept-Encoding: gzip` on `search.do`, the API returns `status: 102`.

**Auth Error:**
```json
{"status": 900, "msg": "Auth failed: check apiKey/appKey.", "routings": []}
```

---

## 7. Common Response Status Codes

| Status | Meaning |
|:------:|---------|
| 0 | Success |
| 100 | Missing required parameters |
| 101-102 | Parameter validation error |
| 107 | Insufficient balance |
| 109 | Daily search limit exceeded |
| 200-299 | Verify/price errors |
| 300-330 | Order/booking errors |
| 800 | Order not found |
| 900 | Authentication failed |
| 9999 | Internal server error |

For detailed error code explanations, look up via MCP: `searchDocumentation("Error Codes")`.

---

## 7b. Rate Limiting & Retry Strategy

Clients should implement a robust retry strategy to handle transient errors and rate limits gracefully.

### Recommended Retry Pattern

```
API Response
    │
    ├── status: 0 → Success → Continue flow
    │
    ├── status in [112, 205, 316] → Transient timeout → Retry with exponential backoff
    │
    ├── status: 109 → Daily quota exceeded → Wait until next UTC day, or request quota increase
    │
    ├── status in [202, 301] → Session/Routing expired → Restart from search or verify
    │
    ├── status: 308 → Price changed → Re-verify and resubmit order
    │
    ├── status in [207, 210, 302, 320] → Availability changed → Restart from search
    │
    ├── status: 113 → Airline maintenance → Retry after 5-10 minutes
    │
    └── status in [900, 9999] → Auth/System → Check credentials, escalate if persistent
```

### Exponential Backoff Algorithm (for transient errors)

| Retry # | Wait Time | Notes |
|:-------:|-----------|-------|
| 1 | 1 second | First retry immediately after brief pause |
| 2 | 2 seconds | |
| 3 | 4 seconds | |
| 4 | 8 seconds | |
| 5 | 15 seconds | Cap at 15 seconds max |
| 6+ | Stop retrying | Log error and escalate |

```python
# Pseudocode
max_retries = 5
for attempt in range(max_retries):
    response = call_api(endpoint, body)
    if response["status"] == 0:
        return response
    if response["status"] not in TRANSIENT_ERRORS:
        raise ApiError(response["status"], response.get("msg"))
    wait = min(2 ** attempt, 15)  # exponential backoff, cap at 15s
    time.sleep(wait)
raise ApiError("Max retries exceeded")
```

### Daily Quota Management

| Quota Type | Limit | Recovery |
|------------|:-----:|----------|
| `priceCompareSearch.do` | 1,000 calls/day | Resets at 00:00 UTC |
| `search.do` | Varies by contract | Contact account manager to increase |
| Other booking endpoints | Varies by contract | — |

**Best practices:**
- Cache search results for frequently queried routes to reduce API calls
- Implement a **circuit breaker**: if consecutive errors exceed a threshold, pause all calls for 30 seconds before resuming
- Monitor `status: 107` (insufficient balance) proactively by checking balance before initiating booking flows
- Log all retry attempts with timestamp, endpoint, status code, and attempt number for debugging

---

## 8. Key Integration Notes

### SessionId Validity
- `sessionId` from `verify.do` is **valid for 2 hours**
- `routingIdentifier` from `search.do` is **valid for up to 6 hours**
- Calling `verify.do` again generates a **new** sessionId — the old one becomes invalid
- Ancillary product codes (`productCode`) are tied to a sessionId — re-verifying invalidates them

### FR (Ryanair) Specific Flow
- FR requires an additional `orderCommit.do` step between `order.do` and `pay.do`
- FR requires a `locale` field (e.g., `"ie/en"`) in `order.do`
- `getOffers.do` may be needed for FR to properly scope the routing

### Name Format
- Passenger names must follow: `LastName/GivenName MiddleName`
- Contact names: same format, Latin letters only

### Field Name Variations
- `search.do` in sandbox may use `outBoundSegments`; in production uses `fromSegments`
- `verify.do` and `priceCompareSearch.do` consistently use `fromSegments`

### Regenerate Order (支付超时重试)

当支付超时时，可调用 **regenerateOrder.do** 重新生单，**无需重复搜索→验价→下单流程**。

```
order.do ──→ pay.do (超时/失败)
               │
               ▼
        regenerateOrder.do ──→ pay.do (重试)
               │
               ▼
         新 orderNo + pnrCode
```

| 对比项 | 常规流程 | regenerateOrder 流程 |
|:------:|----------|---------------------|
| 是否重新搜索 | ❌ | ❌ **不需要** |
| 是否重新验价 | ❌ | ❌ **不需要** |
| 是否重新下单 | ❌ | ❌ **不需要** |
| 输入参数 | sessionId + passengers | `orderNo`（原订单号） |
| 输出 | 新 orderNo | 新 orderNo + pnrCode |

**请求参数:**
```json
{
    "orderNo": "<原订单号>"
}
```

> ⚠️ 沙箱中模拟支付超时的方式：支付时使用错误或不完整的支付参数，或等待 session 过期后尝试支付。

---

## 8b. Ancillary Services (Luggage & Seat Selection)

Ancillary services (baggage and seat selection) are optional add-ons that can be queried and booked as part of the main booking flow. They generate `productCode` values that must be passed into `order.do`'s `passengers[].ancillaries` array.

### Prerequisites

Before calling ancillary APIs, confirm:

| Check | Endpoint / Field | Notes |
|-------|------------------|-------|
| Valid session | `verify.do` → `sessionId` (Flow A) or `getOffers.do` → `offerId` (Flow B) | sessionId valid for 2 hours; productCodes are tied to it |
| Seat selection supported | `search.do` response → `ancillarySupported` field | If `false`, skip seat selection entirely |
| Carrier supports it | Per-airline logic | Not all airlines offer seat selection / prepaid baggage |

> 🔴 **CHECKPOINT · Confirm Ancillary Prerequisites**
> Before calling ancillary APIs, confirm with the client: Is the session/offer still valid? Does the airline support seat selection?
> If the session has expired, re-run `verify.do` or `getOffers.do` first.

---

### getLuggage.do — Query Baggage Options

Query available baggage options for a verified session or offer.

#### Request

```
POST {base}/getLuggage.do
Content-Type: application/json
```

```json
{
    "offerId": "<sessionId or offerId from verify/getOffers>"
}
```

| Parameter | Source | Description |
|-----------|--------|-------------|
| `offerId` | `verify.do` response: `sessionId` (Flow A) or `getOffers.do` response: `offerId` (Flow B) | The session or offer identifier |

#### Response

```json
{
    "status": 0,
    "msg": "Success",
    "data": [
        {
            "name": "1 piece 20kg",
            "productCode": "BAG_LS_STNALC_20KG_1",
            "price": 2500,
            "currency": "CNY",
            "passengerIndex": 0,
            "segmentIndex": 1,
            "maxQuantity": 1,
            "attributes": {
                "weight": 20,
                "unit": "kg",
                "pieces": 1
            }
        },
        {
            "name": "1 piece 32kg",
            "productCode": "BAG_LS_STNALC_32KG_1",
            "price": 4000,
            "currency": "CNY",
            "passengerIndex": 0,
            "segmentIndex": 1,
            "maxQuantity": 1,
            "attributes": {
                "weight": 32,
                "unit": "kg",
                "pieces": 1
            }
        }
    ]
}
```

| Field | Description |
|-------|-------------|
| `productCode` | **Unique code** for the baggage option — pass this into `order.do` ancillaries |
| `passengerIndex` | Which passenger this option applies to (`0` = first passenger) |
| `segmentIndex` | Which segment of the itinerary (`1` = first leg) |
| `maxQuantity` | Max number of this product that can be purchased per passenger |
| `price` | Price in currency units (cents — divide by 100 for display) |

#### Error Codes

| Status | Meaning | Action |
|:------:|---------|--------|
| 0 | Success | Parse `data` array and present options to user |
| 212 | Parameter illegal | Check `offerId` is the correct sessionId/offerId |
| 214 | offerId/sessionId invalid or expired | Re-run `verify.do` or `getOffers.do` |
| 216 | No baggage options available for this route/fare | Proceed without baggage ancillaries |

---

### seatAvailability.do — Query Seat Map

Query the seat map and pricing for a verified session or offer. Not all airlines support this.

#### Request

```
POST {base}/seatAvailability.do
Content-Type: application/json
```

```json
{
    "sessionId": "<sessionId or offerId>",
    "carrier": "LS",
    "outboundSegments": [
        {
            "flightNumber": "LS1411",
            "segmentIndex": 1,
            "depAirport": "STN",
            "arrAirport": "ALC",
            "cabinClass": "1",
            "depTime": "202610180835"
        }
    ]
}
```

| Parameter | Source | Description |
|-----------|--------|-------------|
| `sessionId` | `verify.do` `sessionId` (Flow A) or `getOffers.do` `offerId` (Flow B) | Session or offer identifier |
| `carrier` | From search results | Airline IATA code (e.g., `LS`, `FR`, `VY`) |
| `outboundSegments[].flightNumber` | From search results | Flight number, e.g. `LS1411` |
| `outboundSegments[].segmentIndex` | Segment position (1-based) | `1` for first leg |
| `outboundSegments[].depAirport` | Departure airport code | e.g., `STN` |
| `outboundSegments[].arrAirport` | Arrival airport code | e.g., `ALC` |
| `outboundSegments[].cabinClass` | Cabin class from search | `"1"` = Economy, `"2"` = Business |
| `outboundSegments[].depTime` | Departure datetime | Format: `YYYYMMDDHHmm` |

> ⚠️ For **round-trip** flights, also include an `inboundSegments` array with the same structure.

#### Response

```json
{
    "status": 0,
    "msg": "Success",
    "data": {
        "seatMap": [
            {
                "row": "1",
                "seats": [
                    {
                        "seatNo": "1A",
                        "seatType": "W",
                        "productCode": "SEAT_LS_STNALC_1A_1",
                        "price": 5000,
                        "currency": "CNY",
                        "isAvailable": true,
                        "passengerIndex": 0,
                        "segmentIndex": 1,
                        "characteristics": ["window", "extraLegroom"]
                    },
                    {
                        "seatNo": "1C",
                        "seatType": "A",
                        "productCode": "SEAT_LS_STNALC_1C_1",
                        "price": 3000,
                        "currency": "CNY",
                        "isAvailable": true,
                        "passengerIndex": 0,
                        "segmentIndex": 1,
                        "characteristics": ["aisle"]
                    }
                ]
            }
        ],
        "hasMoreRows": false
    }
}
```

| Field | Description |
|-------|-------------|
| `productCode` | **Unique code** for the seat — pass this into `order.do` ancillaries |
| `seatType` | `W` = Window, `A` = Aisle, `C` = Center |
| `isAvailable` | Whether the seat can be selected |
| `characteristics` | Tags like `extraLegroom`, `window`, `aisle`, `exitRow` |
| `passengerIndex` | Which passenger this seat applies to |
| `segmentIndex` | Which segment of the itinerary |
| `price` | Price in cents (divide by 100 for display) |
| `hasMoreRows` | `true` if there are additional rows not shown in this page |

#### Error Codes

| Status | Meaning | Action |
|:------:|---------|--------|
| 0 | Success | Render seat map for user selection |
| 214 | sessionId/offerId expired | Re-run `verify.do` or `getOffers.do` |
| 218 | Airline does not support seat selection | Proceed without seat ancillaries |
| 219 | Route does not support seat selection | Proceed without seat ancillaries |
| 220 | Parameter illegal | Check request body fields (especially `outboundSegments`) |

---

### Passing productCode into order.do

Once the user selects luggage and/or seats, the `productCode` values must be passed into `order.do` via the `passengers[].ancillaries` array.

#### ancillaries Array Structure

Each ancillary item in the array:

```json
{
    "productCode": "<productCode from getLuggage.do or seatAvailability.do>",
    "segmentIndex": 1
}
```

| Field | Description |
|-------|-------------|
| `productCode` | The exact `productCode` returned by the ancillary API |
| `segmentIndex` | Which flight segment this ancillaries applies to (1-based) |

#### Complete Example: order.do with Baggage & Seat

```json
{
    "sessionId": "a1b2c3d4e5f6g7h8",
    "passengers": [
        {
            "name": "Testpass/Example",
            "passengerType": 0,
            "birthday": "19900101",
            "gender": "M",
            "nationality": "GB",
            "ancillaries": [
                {
                    "productCode": "BAG_LS_STNALC_20KG_1",
                    "segmentIndex": 1
                },
                {
                    "productCode": "SEAT_LS_STNALC_1A_1",
                    "segmentIndex": 1
                }
            ]
        }
    ],
    "contact": {
        "name": "Testpass/Example",
        "email": "test@example.com",
        "mobile": "0044-71234567890"
    }
}
```

> ⚠️ **Important:** Baggage `productCode` values and seat `productCode` values both go into the **same** `ancillaries` array. They are differentiated by their `productCode` prefix.

#### Common Errors

| Status | Meaning | Action |
|:------:|---------|--------|
| 320 | Selected seat(s) no longer available | Re-run `seatAvailability.do` → let user pick different seat → resubmit |
| 321 | Selected baggage option no longer available | Re-run `getLuggage.do` → let user pick different option → resubmit |
| 323 | Invalid passenger info or ancillary mismatch | Check that passenger count/index matches ancillary `passengerIndex` |

#### Complete Call Flow

```
                    ┌──────────────────┐
                    │  verify.do ──────┼── sessionId
                    │  or getOffers.do │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
    ┌─────────────────┐ ┌──────────────────────┐
    │ getLuggage.do   │ │ seatAvailability.do   │
    │ sessionId/offerId│ │ sessionId/offerId     │
    └────────┬────────┘ │ + outboundSegments    │
             │          └──────────┬───────────┘
             ▼                     ▼
    productCode            productCode
    (BAG_xxx)              (SEAT_xxx)
             │                     │
             └──────────┬──────────┘
                        ▼
               ┌─────────────────┐
               │    order.do     │
               │  ancillaries: [ │
               │    {productCode}│
               │    {productCode}│
               │  ]              │
               └─────────────────┘
```

## 9. Flow-Specific Guidance

### When to Use Flow A (Search → Verify → Order → Pay)

**Typical client profiles:**
- OTA (Online Travel Agency) with their own flight search UI
- Meta-search engines needing to quote and book
- Travel booking platforms that want full control over the shopping experience

**Key considerations:**
- Search results expire after 6 hours (rerun `search.do` if expired)
- Verify step confirms current pricing before booking
- Can include ancillaries (luggage, seats) in the booking flow

### When to Use Flow B (Get Offer → Order → Pay)

**Typical client profiles:**
- TMC (Travel Management Company) with pre-negotiated itineraries
- Aggregators who already have flight data from other sources
- Partners who need a quick price check without full search
- Clients who want to bypass search caching and get real-time data

**Key considerations:**
- No separate verify step — `getOffers.do` returns a direct `offerId`
- Get Offer also supports ancillary queries (`getLuggage.do`, `seatAvailability.do`)
- Returns the same booking requirements structure as verify

---

## 9b. Webhook / Asynchronous Notifications

Atlas supports webhooks to notify clients of asynchronous events (ticketing status changes, order updates, etc.). This eliminates the need for polling.

### Webhook Flow

```
Client System                   Atlas Platform
    │                                │
    │  POST order.do                 │
    │───────────────────────────────>│
    │  response: orderNo             │
    │<───────────────────────────────│
    │                                │
    │           [asynchronous processing]
    │                                │
    │  ← POST /your-webhook/url      │  (order status changed)
    │  ← {eventType, orderNo,        │
    │  ←  orderStatus, timestamp}    │
    │                                │
    │  POST pay.do                   │
    │───────────────────────────────>│
    │  response: status 0            │
    │<───────────────────────────────│
    │                                │
    │  ← POST /your-webhook/url      │  (ticket issued)
    │  ← {eventType, orderNo,        │
    │  ←  ticketStatus, timestamp}   │
```

### Supported Webhook Events

Atlas supports the following webhook notification types. Configure which ones you want to receive via **ATRIP → Profile → My Profile → Notification → Webhook tab**.

| Notification Type | Trigger Condition | Payload Highlights |
|-------------------|-------------------|-------------------|
| **Ticketing Completion** | Ticket successfully issued | `orderNo`, `ticketStatus: 2`, `ticketNos`, `pnrCode` |
| **Refund Status** | Refund processing update (submitted / completed / rejected) | `orderNo`, `refundAmount`, `refundStatus: 0-6` |
| **Incident Notification via API** | Schedule change detected by Atlas flight monitoring | `orderNo`, `incidentType: "schedule_change"`, `oldTime`, `newTime`, `flightNumber` |
| **Incident Notification via Airline Email** | Schedule change email received from airline | `orderNo`, `incidentType: "schedule_change_email"`, `emailContent` |
| **Airline Status** | Airline operational status change (maintenance / strike / system outage) | `airline`, `status`, `affectedPeriod` |
| **Emails from Airline** | Airline sends email to booking contact (forwarded via Atlas Email Service) | `orderNo`, `emailSubject`, `emailBody`, `attachmentLinks` |

### Webhook Configuration

1. **Register webhook URL** via ATRIP Portal → Settings → Webhooks
2. **Provide a publicly accessible HTTPS endpoint** on your server
3. **Respond with HTTP 200** within 5 seconds to acknowledge receipt
4. **Implement idempotency**: webhook events include an `eventId` — deduplicate on this field
5. **Retry policy**: Atlas retries failed deliveries up to 3 times (intervals: 1min, 5min, 30min)

### Webhook Payload Examples

**Ticketing Completion:**
```json
{
    "notificationType": "Ticketing Completion",
    "orderNo": "ATL20261018000123",
    "timestamp": "2026-10-18T09:15:30Z",
    "data": {
        "orderStatus": 2,
        "ticketStatus": 2,
        "ticketNos": ["9321234567890"],
        "pnrCode": "ABC123"
    }
}
```

**Incident Notification (Schedule Change):**
```json
{
    "notificationType": "Incident Notification via API",
    "orderNo": "ATL20261018000123",
    "timestamp": "2026-10-17T14:30:00Z",
    "data": {
        "incidentType": "schedule_change",
        "flightNumber": "LS1411",
        "oldDepartureTime": "2026-10-18T08:35:00",
        "newDepartureTime": "2026-10-18T10:15:00",
        "oldArrivalTime": "2026-10-18T12:00:00",
        "newArrivalTime": "2026-10-18T13:40:00",
        "reasonCode": "AIRLINE_SCHEDULE"
    }
}
```

**Airline Status:**
```json
{
    "notificationType": "Airline Status",
    "airline": "FR",
    "status": "SYSTEM_OUTAGE",
    "affectedPeriod": {
        "start": "2026-10-18T00:00:00Z",
        "end": "2026-10-18T23:59:59Z"
    },
    "description": "Ryanair reservation system scheduled maintenance"
}
```

### Ticketing Delay Notification

When ticketing is delayed (due to airline system issues, sold out, awaiting confirmation, etc.), Atlas automatically routes the order to the Exception Queue and sends a delay notification via webhook or other channels.

**Configuration path:** ATRIP → Profile → My Profile → Notification → Email Notification

**Possible delay reasons:**
- System Issue
- Sold Out
- Awaiting Airline Confirmation
- Awaiting Customer Confirmation
- Airline System Issue
- Payment Issue

> When the delay reason is **"Awaiting Customer Confirmation"**, the system automatically creates a Service Request — the client must reply with the required information before ticketing can proceed.

### Polling Fallback

If webhooks are not configured, fall back to polling `queryOrderDetails.do`:

| Polling Interval | Phase |
|:----------------:|-------|
| Every 30 seconds | First 5 minutes after payment |
| Every 2 minutes | After 5 minutes, up to 30 minutes |
| Every 10 minutes | After 30 minutes |

Stop polling when `ticketStatus` reaches `2` (ticketed) or `-3` (cancelled).

---

## 9c. Post-Booking Flow

In addition to the main booking flow, Atlas provides post-booking APIs for the following scenarios: post-booking ancillary (adding baggage/services after ticketing), refund, void, and order cancellation. These APIs are called **after ticketing is complete**.

### Post-Booking Flow Overview

```
        Ticketed (ticketStatus: 2)
                  │
      ┌───────────┼─────────────┬──────────────┐
      ▼           ▼             ▼              ▼
 ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────┐
 │Post-    │ │ Refund  │ │  Void    │ │  Cancel      │
 │Booking  │ │         │ │          │ │  Order       │
 │Ancillary│ │         │ │          │ │              │
 └────┬────┘ └────┬────┘ └────┬───┘ └──────┬───────┘
      │           │           │            │
      ▼           ▼           ▼            ▼
  Ancillary    Refund      Void        Order
  Added        Complete    Complete    Cancelled
```

| Scenario | When to Call | Key Endpoints |
|:---------|-------------|---------------|
| **Post-Booking Ancillary** | After ticketing, add baggage/services to the same order | `postBookingAncillarySearch.do` → `postBookingAncillaryOrder.do` |
| **Refund** | After ticketing, when a passenger cannot travel | `refund.do` (or query rules first via `queryRefundRules.do`) |
| **Void** | Shortly after ticketing (airline window) | `voidOrder.do` / `queryVoidOrders.do` |
| **Cancel Order** | Cancel before payment | Can cancel any time before calling `pay.do` |

---

### Post-Booking Ancillary

After ticketing, if a passenger needs additional baggage or services, use the post-booking ancillary flow instead of re-booking.

#### Step 1: Search Available Ancillaries

```
POST {base}/postBookingAncillarySearch.do
Content-Type: application/json
```

```json
{
    "ticketOrderNo": "ATL20261018000123",
    "ancillaryCategory": "BAGGAGE"
}
```

| Parameter | Description |
|-----------|-------------|
| `ticketOrderNo` | Ticketed order number (from `order.do` response) |
| `ancillaryCategory` | Category: `BAGGAGE`, `SEAT`, `SERVICE` |

**Response Example:**

```json
{
    "status": 0,
    "msg": "Success",
    "data": [
        {
            "name": "Extra 20kg",
            "productCode": "BAG_POST_LS_20KG",
            "price": 3000,
            "currency": "CNY",
            "passengerIndex": 0,
            "maxQuantity": 1
        }
    ]
}
```

#### Step 2: Submit Ancillary Order

```
POST {base}/postBookingAncillaryOrder.do
Content-Type: application/json
```

```json
{
    "sessionId": "<sessionId from latest verify>",
    "ticketOrderNo": "ATL20261018000123",
    "passengers": [
        {
            "name": "Testpass/Example",
            "passengerType": 0,
            "ancillaries": [
                {
                    "productCode": "BAG_POST_LS_20KG",
                    "segmentIndex": 1
                }
            ]
        }
    ]
}
```

| Parameter | Source | Description |
|-----------|--------|-------------|
| `sessionId` | Latest `verify.do` or `getOffers.do` session | Valid session required to bind ancillary |
| `ticketOrderNo` | Ticketed order number | Must be ticketed (`ticketStatus: 2`) |
| `passengers[].ancillaries[].productCode` | From `postBookingAncillarySearch.do` response | Product code for the ancillary item |

#### Error Codes

| Status | Meaning | Action |
|:------:|---------|--------|
| 0 | Success | Ancillary added |
| 214 | sessionId expired | Re-run `verify.do` to get a new session |
| 330 | Order not eligible for post-booking | Order may not be ticketed or already refunded |
| 332 | Product no longer available | Re-search available ancillaries |

---

### Refund

Use when a refund is needed after ticketing. Refund rules vary by airline (whether refundable, penalty fees). It is recommended to query refund rules first.

#### Query Refund Rules

```
POST {base}/queryRefundRules.do
Content-Type: application/json
```

```json
{
    "orderNo": "ATL20261018000123"
}
```

**Response Example:**

```json
{
    "status": 0,
    "msg": "Success",
    "data": {
        "refundable": true,
        "refundPenalty": 5000,
        "currency": "CNY",
        "refundDeadline": "20261020T235959",
        "perPassenger": true,
        "notes": "Refund allowed up to 24h before departure"
    }
}
```

| Field | Description |
|-------|-------------|
| `refundable` | Whether the ticket is refundable |
| `refundPenalty` | Refund penalty fee (per passenger, in cents) |
| `refundDeadline` | Refund deadline timestamp |
| `perPassenger` | Whether the penalty is charged per passenger |
| `notes` | Airline refund policy notes |

#### Submit Refund

```
POST {base}/refund.do
Content-Type: application/json
```

```json
{
    "orderNo": "ATL20261018000123",
    "passengers": [
        {"name": "Testpass/Example", "passengerType": 0}
    ],
    "refundReason": "Passenger itinerary change",
    "contact": {
        "name": "Testpass/Example",
        "email": "test@example.com",
        "mobile": "0044-71234567890"
    }
}
```

| Parameter | Description |
|-----------|-------------|
| `orderNo` | Ticketed order number |
| `passengers[]` | Passengers to refund (partial refund supported) |
| `refundReason` | Reason for refund |

**Response Example:**

```json
{
    "status": 0,
    "msg": "Success",
    "data": {
        "orderNo": "ATL20261018000123",
        "refundStatus": 0,
        "refundAmount": 150000,
        "currency": "CNY",
        "refundNo": "RF2026101800001"
    }
}
```

| Field | Description |
|-------|-------------|
| `refundStatus` | `0`=Atlas processing, `1`=Airline processing, `2`=Refunded, `3`=Airline refunding, `4`=Rejected, `5`=Completed, `6`=Cancelled |
| `refundAmount` | Actual refund amount (cents) |
| `refundNo` | Refund reference number for follow-up queries |

#### Query Refund Status

```
POST {base}/queryRefundStatus.do
Content-Type: application/json
```

```json
{
    "orderNo": "ATL20261018000123"
}
```

#### Error Codes

| Status | Meaning | Action |
|:------:|---------|--------|
| 0 | Success / Refund submitted | Wait for async processing |
| 107 | Insufficient balance for refund | Check account balance |
| 340 | Order not refundable | This order/ticket does not meet airline refund rules |
| 341 | Outside refund window | Past the airline refund deadline |
| 342 | Partial refund not supported | Airline does not support partial refund |
| 800 | Order not found | Verify the orderNo |

---

### Void

Within a short window after ticketing (typically 24 hours, varies by airline), an order can be voided **without refund penalty**. After the void window, use the refund flow instead.

> ⚠️ **Void vs Refund:**
> - **Void**: Cancel shortly after ticketing — airline treats as "not issued", no penalty or minimal penalty
> - **Refund**: Cancel at any time — airline charges refund penalty per policy
> - **Check the airline window first** — use void within the window, use refund after it expires

#### Query Void Status

```
POST {base}/queryVoidOrders.do
Content-Type: application/json
```

```json
{
    "orderNo": "ATL20261018000123"
}
```

**Response Example:**

```json
{
    "status": 0,
    "msg": "Success",
    "data": {
        "orderNo": "ATL20261018000123",
        "voidable": true,
        "voidDeadline": "20261019T235959",
        "voidStatus": -1,
        "voidPenalty": 0
    }
}
```

| Field | Description |
|-------|-------------|
| `voidable` | Whether within the void window |
| `voidDeadline` | Void deadline timestamp |
| `voidStatus` | `-1`=Not processed, `0`=Atlas processing, `1`=Airline processing, `2`=Refunded/voided, `3`=Airline refunding, `4`=Rejected, `5`=Completed, `6`=Cancelled |
| `voidPenalty` | Void penalty fee (typically 0) |

#### Execute Void

```
POST {base}/voidOrder.do
Content-Type: application/json
```

```json
{
    "orderNo": "ATL20261018000123"
}
```

#### Error Codes

| Status | Meaning | Action |
|:------:|---------|--------|
| 0 | Void submitted | Wait for async processing |
| 350 | Void window expired | Past the void window — use refund flow instead |
| 351 | Order not voidable | Order may be partially used or already voided |
| 352 | Airline rejected void | Contact airline or use refund flow |

---

### Cancel Order

Orders can be cancelled **before payment**. Paid orders must go through void or refund instead.

```
POST {base}/cancelOrder.do
Content-Type: application/json
```

```json
{
    "orderNo": "ATL20261018000123"
}
```

#### Error Codes

| Status | Meaning | Action |
|:------:|---------|--------|
| 0 | Order cancelled | Order successfully cancelled |
| 360 | Cannot cancel paid order | Order already paid — use void or refund |
| 361 | Order already cancelled | Order is already in cancelled status |
| 362 | Cancellation not allowed | This order type does not support cancellation |

---

### Post-Booking Decision Tree

```
Order ticketed (ticketStatus: 2)
     │
     ├── Need to add baggage/services?
     │   └── YES → Post-Booking Ancillary flow
     │
     ├── Need to cancel order?
     │   │
     │   ├── Order already paid?
     │   │   ├── Within void window? → Void flow
     │   │   └── Outside void window? → Refund flow
     │   │
     │   └── Not paid yet? → Cancel order
     │
     └── Need to check status?
         └── queryOrderDetails.do or queryRefundStatus.do
```

---

## 10. Code Generation Guidelines

> 🔴 **CHECKPOINT · Confirm Code Generation Requirements**
> Confirm with the client: What programming language? Which flow (Flow A / Flow B)? Are ancillary examples needed?
> Then proceed to code template selection and adaptation.

When generating code for a client:

1. **Determine the client's language** (Python, PHP, Java, Node.js, Go, C#, etc.)
2. **Use the correct flow** (Flow A or Flow B based on their scenario)
3. **Use sandbox credentials** in examples (`x-atlas-client-id: sandbox_credential`)
4. **Use realistic but non-functional test data** — sandbox test routes from `references/integration-scenarios.md`
5. **Include error handling** for common status codes
6. **Add comments** explaining the data chaining between steps
7. **Point to ATRIP portal** for credential management and order viewing

**Refer to:** `references/code-generation-guide.md` for multi-language templates.

---

## 11. Common Client Errors & Anti-Pattern Blacklist

> ⚠️ These are recurring errors observed during Atlas API integration. **Reviewing each item can prevent 90% of integration issues.**

| # | Anti-Pattern | Why It's Wrong | Correct Approach |
|---|-------------|----------------|------------------|
| 1 | **Using `priceCompareSearch.do` as a booking price source** | This endpoint is for pre-sale price comparison only (1,000 calls/day limit); returned prices are not suitable for production booking | Use `verify.do` (Flow A) or `getOffers.do` (Flow B) as the booking price confirmation source |
| 2 | **Skipping `verify.do` and calling `order.do` directly** | Without verify, there is no sessionId, no price validation, and ancillary APIs cannot be queried | Always call `verify.do` first to get a `sessionId`, then pass it to `order.do` |
| 3 | **Calling `search.do` without `Accept-Encoding: gzip`** | API returns `status: 102`, causing search failure | Add `Accept-Encoding: gzip` to the `search.do` request headers |
| 4 | **Calling `verify.do` multiple times in the same session** | Each `verify.do` call generates a new sessionId; the old one is invalidated and all previously obtained ancillary productCodes are lost | Use the sessionId immediately after each `verify.do` call; if re-verification is needed, re-fetch all productCodes |
| 5 | **Using production credentials in the sandbox environment** | Credentials are bound to their environment; production credentials fail auth on sandbox URLs | Use sandbox credentials + `https://sandbox.atriptech.com` for testing; use production credentials + production URLs for live |
| 6 | **Missing `locale` field in `order.do` (Ryanair)** | FR order creation fails with `status: 307` | Always include the `locale` field for FR orders, e.g. `"ie/en"` |
| 7 | **Skipping `orderCommit.do` (Ryanair)** | FR requires an additional commit step; payment fails without it | FR orders must call `orderCommit.do` between `order.do` and `pay.do` |
| 8 | **Using an expired sessionId to query ancillaries** | sessionId is valid for only 2 hours; `getLuggage.do` or `seatAvailability.do` return `status: 214` when expired | Check session validity; re-run `verify.do` or `getOffers.do` if expired |
| 9 | **Not handling webhook idempotency** | The same event may be delivered multiple times, causing duplicate order processing | Use `eventId` for deduplication — idempotent webhook handling |
| 10 | **No retry strategy** | Transient errors (timeout, airline maintenance) break the flow without retries | Implement 5-attempt exponential backoff (1s→2s→4s→8s→15s) and circuit breaker pattern |
| 11 | **Mixing `sessionId` and `offerId` in `order.do`** | The two parameters are mutually exclusive; passing both causes parameter conflicts | Flow A uses `sessionId`; Flow B uses `offerId` — never mix them |
| 12 | **Mismatched `passengerIndex` in ancillaries array** | Baggage/seat assigned to the wrong passenger | Ensure each ancillary's `passengerIndex` matches the corresponding entry in the `passengers` array |

### Pre-Launch Checklist

Before going live, confirm each item:

- [ ] Do NOT use `priceCompareSearch.do` for booking prices
- [ ] Every booking flow includes a verify step (or getOffers)
- [ ] `search.do` request includes `Accept-Encoding: gzip`
- [ ] sessionId used within validity period
- [ ] FR orders include `locale` field + `orderCommit.do`
- [ ] Webhook idempotency is implemented
- [ ] Exponential backoff retry is implemented