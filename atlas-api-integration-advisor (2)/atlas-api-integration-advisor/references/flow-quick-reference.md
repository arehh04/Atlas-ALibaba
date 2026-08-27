# API Flow Quick Reference

Quick reference of the key endpoints used in each booking flow.

> 📖 **For complete ancillary service guidance (prerequisites, response parsing, data chaining to order.do), see SKILL.md §8b — Ancillary Services.**
>
> 📖 **For post-booking flows, see SKILL.md §9c — Post-Booking.**

---

## Flow A: Search → Verify → Order → Pay

### 1. search.do — Search Flights
```
POST {base}/search.do
Headers: x-atlas-client-id, x-atlas-client-secret, Accept-Encoding: gzip
```
```json
{
    "tripType": "1",
    "adultNum": 1,
    "childNum": 0,
    "infantNum": 0,
    "fromCity": "STN",
    "toCity": "ALC",
    "fromDate": "20261018",
    "airlines": ["LS"]
}
```

### 2. verify.do — Verify Price
```
POST {base}/verify.do
```
```json
{
    "routingIdentifier": "<from search response>"
}
```

### 3. [Optional] getLuggage.do — Query Baggage
```
POST {base}/getLuggage.do
```
```json
{"offerId": "<sessionId from verify>"}
```

### 4. [Optional] seatAvailability.do — Query Seat Map
```
POST {base}/seatAvailability.do
```
```json
{
    "sessionId": "<sessionId from verify>",
    "carrier": "LS",
    "outboundSegments": [{
        "flightNumber": "LS1411",
        "segmentIndex": 1,
        "depAirport": "STN",
        "arrAirport": "ALC",
        "cabinClass": "1",
        "depTime": "202610180835"
    }]
}
```

### 5. order.do — Create Booking
```
POST {base}/order.do
```
```json
{
    "sessionId": "<sessionId from verify>",
    "passengers": [{
        "name": "LastName/GivenName",
        "passengerType": 0,
        "birthday": "20050606",
        "gender": "F",
        "nationality": "GB",
        "ancillaries": [
            {"productCode": "<baggage_or_seat_code>", "segmentIndex": 1}
        ]
    }],
    "contact": {
        "name": "LastName/GivenName",
        "email": "test@example.com",
        "mobile": "0086-13928109091"
    }
}
```

### 6. [FR only] orderCommit.do
```
POST {base}/orderCommit.do
```

### 7. pay.do — Payment
```
POST {base}/pay.do
```
```json
{
    "orderNo": "<from order.do>",
    "paymentMethod": 1
}
```

### 8. queryOrderDetails.do — Check Status
```
POST {base}/queryOrderDetails.do
```
```json
{"orderNo": "<from order.do>"}
```

### 9. [Payment Timeout] regenerateOrder.do — 支付超时重新生单
支付超时后调用，无需重复搜索→验价→下单。
```
POST {base}/regenerateOrder.do
```
```json
{"orderNo": "<原订单号 from order.do>"}
```

---

## Flow B: GetOffer → Order → Pay

### 1. getOffers.do — Get Price Quote
```
POST {base}/getOffers.do
```

### 2. [Optional] getLuggage.do — using offerId
```
POST {base}/getLuggage.do
Body: {"offerId": "<offerId from getOffers>"}
```

### 3. [Optional] seatAvailability.do — using offerId
```
POST {base}/seatAvailability.do
Body: (same as Flow A but use "offerId" instead of "sessionId")
```

### 4. order.do — using offerId
```
POST {base}/order.do
Body: {"offerId": "<offerId from getOffers>", "passengers": [...], "contact": {...}}
```

### 5. pay.do — Payment
```
POST {base}/pay.do
Body: (same as Flow A)
```

---

## Price Compare (NOT a booking flow)

```
POST {base}/priceCompareSearch.do
```

Same request format as `search.do`. Returns routing data for comparison only.
**Do NOT use for production booking.**

---

## Post-Booking Quick Reference

### Post-Booking Ancillary

```
# Step 1: Search available ancillaries
POST {base}/postBookingAncillarySearch.do
Body: {"ticketOrderNo": "<orderNo>", "ancillaryCategory": "BAGGAGE"}

# Step 2: Submit ancillary order
POST {base}/postBookingAncillaryOrder.do
Body: {
    "sessionId": "<sessionId>",
    "ticketOrderNo": "<orderNo>",
    "passengers": [{"name": "...", "passengerType": 0, "ancillaries": [...]}]
}
```

### Refund

```
# Step 1 (optional): Query refund rules
POST {base}/queryRefundRules.do
Body: {"orderNo": "<orderNo>"}

# Step 2: Submit refund
POST {base}/refund.do
Body: {"orderNo": "<orderNo>", "passengers": [...], "refundReason": "..."}

# Step 3: Query refund status
POST {base}/queryRefundStatus.do
Body: {"orderNo": "<orderNo>"}
```

### Void

```
# Step 1: Query void status
POST {base}/queryVoidOrders.do
Body: {"orderNo": "<orderNo>"}

# Step 2: Execute void
POST {base}/voidOrder.do
Body: {"orderNo": "<orderNo>"}
```

### Cancel Order

```
POST {base}/cancelOrder.do
Body: {"orderNo": "<orderNo>"}
```

---

## Data Chaining Summary

```
search.do ────── routingIdentifier ──────→ verify.do ── sessionId ──┐
                                                                     │
priceCompareSearch.do ── fid/routingIdentifier ──→ order.do (no verify) ──→ pay.do
                                                                     │
getOffers.do ────────── offerId ─────────────────→ order.do ─────────→ pay.do
                                                                    │
                                              sessionId/offerId ────┤
                                              (for luggage/seat)     │
                                                                    │
                                                              post-booking
                                                              ancillary APIs
```