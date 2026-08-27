# Common Integration Issues

Common issues clients encounter during Atlas API integration and how to diagnose/resolve them.

> 📖 **For full ancillary request/response schemas, see SKILL.md §8b — Ancillary Services.**
>
> 📖 **For post-booking flows, see SKILL.md §9c — Post-Booking.**

---

## Authentication Issues

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| `status: 900` | Incorrect credentials | Verify client ID and secret with ATRIP credentials |
| `status: 900` | Account not activated | Contact account manager to check account status |
| `status: 9999` | Missing header (often `x-atlas-client-secret`) | Check all required headers are present |
| `status: 102` on search.do | Missing `Accept-Encoding: gzip` | Add the gzip header to search.do requests |

---

## Search Issues

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| Empty results with no error | No flights available for route/date | Check airline website for flight availability |
| `status: 107` | Insufficient balance | Top up account |
| `status: 109` | Daily search limit exceeded | Wait for next day or contact account manager |
| `status: 112` | Search timeout | Retry with smaller result set or later |
| `status: 113` | Airline under maintenance | Wait and retry |
| `status: 114` | No flights for this date/route | Try different date or route |

---

## Verify Issues

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| `status: 202` | routingIdentifier expired (> 6 hours) | Run search.do again for fresh routingIdentifier |
| `status: 207` | Flight no longer available | Run search.do again for updated results |
| `status: 210` | Fare family sold out | Search again and select different fare |

---

## Order Issues

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| `status: 301` | sessionId expired (> 2 hours) | Run verify.do again for fresh sessionId |
| `status: 302` | Flight sold out | Start from search again |
| `status: 307` | Missing or invalid `locale` (FR) | Add correct locale field, e.g., `"ie/en"` |
| `status: 308` | Price changed | Re-verify and re-submit order |
| `status: 320` | Selected seats no longer available | Re-verify, re-fetch seat map, select different seats |
| `status: 323` | Invalid contact email format | Check email format |
| `status: 325` | Airline rejected passenger | Check passenger name format and details |
| `status: 327` | Passenger info doesn't meet requirements | Check bookingRequirement from verify response |

---

## Get Luggage Issues

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| `status: 212` | Parameter illegal | Check offerId/sessionId is valid |
| `status: 214` | offerId/sessionId invalid or expired | Re-run verify.do or getOffers.do |

---

## Seat Selection Issues

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| `status: 214` | sessionId/offerId expired | Re-verify for fresh sessionId |
| `status: 218` | Airline doesn't support seat selection | Proceed without seat selection |
| `status: 219` | Route doesn't support seat selection | Proceed without seat selection |
| `status: 220` | Parameter illegal | Check request body |
| `status: 320` on order.do | Selected seat already taken | Re-verify → re-fetch seats → choose different seat |

---

## Payment Issues

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| `status: 107` | Insufficient balance | Top up account |
| `status: 329` | No payment method available | Check account currency/configuration |

---

## Post-Booking Issues

### Post-Booking Ancillary

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| `status: 214` | sessionId expired | Re-run `verify.do` or `getOffers.do` |
| `status: 330` | Order not eligible for post-booking | Order may not be ticketed yet or already refunded |
| `status: 332` | Product no longer available | Re-search available ancillaries |

### Refund

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| `status: 107` | Insufficient balance to process refund | Check account balance |
| `status: 340` | Order not refundable | Check refundRules from search or query order |
| `status: 341` | Outside refund window | Refund deadline has passed |
| `status: 342` | Partial refund not supported | Must refund all passengers |
| `status: 800` | Order not found | Check orderNo |

### Void

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| `status: 350` | Void window expired | Outside airline void window → Use refund flow instead |
| `status: 351` | Order not voidable | Order may be partially used or already voided |
| `status: 352` | Airline rejected void | Contact airline or use refund flow |

### Cancel Order

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| `status: 360` | Cannot cancel paid order | Order already paid → Use void or refund |
| `status: 361` | Order already cancelled | Order is already in cancelled status |
| `status: 362` | Cancellation not allowed | This order type does not support cancellation |

---

## Order Status Values

From `queryOrderDetails.do`:

| Value | Meaning |
|:-----:|---------|
| `0` | Unpaid |
| `1` | Ticketing in Process |
| `2` | Ticketed |
| `-3` | Cancelled |

## Void Status Values

From `queryVoidOrders.do`:

| Value | Meaning |
|:-----:|---------|
| `0` | Atlas Processing |
| `1` | Airline Processing |
| `2` | Refunded / Voided |
| `3` | Airline Refunding |
| `4` | Rejected |
| `5` | Fulfillment Done |
| `6` | Withdrew |

---

## Typical Retry Pattern

```python
# Pseudo-code for handling common errors
def handle_api_response(response):
    if response.status == 0:
        return success()
    elif response.status in [112, 205, 316]:  # timeout
        retry_with_backoff()
    elif response.status in [202, 301]:  # expired session/routing
        restart_from_search_or_verify()
    elif response.status == 308:  # price changed
        re_verify_and_resubmit()
    elif response.status in [207, 210, 302, 320]:  # availability changed
        restart_from_search()
    elif response.status in [900, 9999]:  # auth/system
        check_credentials_and_headers()
    else:
        log_error_and_escalate(response.status, response.msg)
```

> **For exact error code definitions, use MCP:** `searchDocumentation("Error Codes")`