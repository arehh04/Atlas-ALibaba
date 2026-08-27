# Integration Scenarios & Sandbox Test Data

This reference helps identify which integration scenario a client fits into and provides sandbox test routes for each. It also includes UAT-level test scenarios covering connecting flights, ancillary services, post-ticketing operations, refunds, voids, and payment retry flows.

---

## 1. Client Scenario Identification

| Scenario | Client Type | Recommended Flow | Key Characteristics |
|----------|-------------|:----------------:|---------------------|
| **Full Booking OTA** | Online Travel Agency | Flow A (Search→Verify→Order→Pay) | Atlas is primary shopping source; needs full flight display + booking + ancillaries |
| **Get Offer Booker** | TMC / Aggregator | Flow B (GetOffer→Order→Pay) | Has own flight data; needs Atlas for price confirmation & booking only |
| **Price Comparison** | Flight Deck / Blogger | priceCompareSearch.do **only** (NO booking) | Only needs fare discovery; no ticketing required |
| **Ancillary Only** | Post-booking service | postBookingAncillarySearch→Order | Already has ticketed orders; wants to add baggage post-ticketing |
| **Hybrid** | Multi-channel client | Both Flow A + Flow B | Uses search for some routes, getOffer for others |

---

## 2. Sandbox Test Routes

### Flow A Test: Standard Search → Verify → Order → Pay

> 💡 **Tip:** Use future dates (at least 7 days from today). The dates below are **examples** — adjust the year/month/day to be a valid future date. Dates >= 45 days out are preferred for wider availability.

| Airline | Route | Trip Type | Test Scenarios | Notes |
|---------|-------|:---------:|----------------|-------|
| LS (Jet2) | STN→ALC | One-way | Search → Verify → Order → Pay, seat, baggage | Good baseline test |
| VY (Vueling) | LON→BCN | One-way | Booking, fare families | Budget carrier |
| G4 (Allegiant) | LAS→MEM | One-way | US domestic LCC | |
| A3 (Aegean) | TLS→CAI | One-way | Full-service carrier | |
| 3U (Sichuan Airlines) | CAN→TFU | One-way | Chinese domestic carrier | |

#### 联程航线测试 (Connecting / Multi-Segment)

| Airline | Route | Trip Type | Test Scenarios | Notes |
|---------|-------|:---------:|----------------|-------|
| **6E (IndiGo)** | **AMS→MAA** | Connecting | **Search → Verify → Order → Pay (multi-segment)** | 联程转机，验证多段 `fromSegments` 路由 |
| **6E (IndiGo)** | **COK→DXB** | One-way | Booking + **seat selection** | 选座测试推荐路线 |

#### 直达航线测试 (Direct Flight)

| Airline | Route | Trip Type | Test Scenarios | Notes |
|---------|-------|:---------:|----------------|-------|
| **FA (FlySafair)** | **DUR→CPT** | One-way | Direct booking | 直达航线测试推荐路线 |

#### VCC 虚拟信用卡支付流程

| Airline | Route | Trip Type | Test Scenarios | Notes |
|---------|-------|:---------:|----------------|-------|
| **7C (Jeju Air)** | **PUS→CJU** | One-way | **VCC payment flow** → Order → Pay (VCC) | 韩国国内航线，支持虚拟信用卡支付验证 |

### Flow B Test: GetOffer → Order → Pay

| Airline | Route | Trip Type | Notes |
|---------|-------|:---------:|-------|
| Same airlines as Flow A | Any known flight number | Any | Call getOffers.do with specific flight info |
| **7C (Jeju Air)** | **PUS→CJU** | One-way | Also works with getOffers when you know the itinerary |

### FR (Ryanair) Special Flow Test

| Airline | Route | Trip Type | Notes |
|---------|-------|:---------:|-------|
| FR | DUB→LON | One-way | FR requires `orderCommit.do` + `locale` field |
| FR | STN→ALC | One-way | FR test; requires proper locale setting |

---

## 3. Baggage (Inflow) Test Routes

> 适用于测试在预订流程中附加行李（Inflow 行李）。大部分基础航司均支持 inflow 行李。

| Airline | Route | Trip Type | Test Scenarios | Notes |
|---------|-------|:---------:|----------------|-------|
| **IX (Air India Express)** | **BOM→IXR** | One-way | Search → Verify → **getLuggage.do** → Order (with ancillaries) → Pay | 基本航司，行李选项稳定 |
| LS (Jet2) | STN→ALC | One-way | Search → Verify → **getLuggage.do** → Order → Pay | 已验证的基础行李测试路线 |
| VY (Vueling) | LON→BCN | One-way | Search → Verify → **getLuggage.do** → Order → Pay | 行李产品代码可参考 |

---

## 4. Seat Selection Test Routes

| Airline | Route | Trip Type | Test Scenarios | Notes |
|---------|-------|:---------:|----------------|-------|
| **6E (IndiGo)** | **COK→DXB** | One-way | Search → Verify → **seatAvailability.do** → Order (with seat ancillaries) → Pay | 选座测试推荐路线 |
| LS (Jet2) | STN→ALC | One-way | Search → Verify → **seatAvailability.do** → Order → Pay | 备选选座路线 |

---

## 5. Regenerate Order (支付超时重试)

当支付超时时，可调用 **regenerateOrder.do** 重新生单，**无需重复搜索→验价→下单流程**。

### 流程图

```
order.do ──→ pay.do (超时/失败)
               │
               ▼
        regenerateOrder.do ──→ pay.do (重试)
               │
               ▼
         新 orderNo + pnrCode
```

### 请求参数

```json
{
    "orderNo": "<原订单号>"
}
```

### 测试路线

| Airline | Route | Test Flow | Notes |
|---------|-------|-----------|-------|
| 任意 Flow A 已验证路线 | — | Order → Pay (模拟超时) → **regenerateOrder.do** → Pay | 验证 regenerate 后获得新 orderNo |
| **7C (Jeju Air)** | **PUS→CJU** | Search → Verify → Order → Pay(超时) → **regenerateOrder.do** → Pay | 推荐测试组合 |

> ⚠️ 沙箱中模拟支付超时的方式：支付时使用错误或不完整的支付参数，或者等待 session 过期后尝试支付。

### 与常规下单对比

| 场景 | 常规流程 | regenerateOrder 流程 |
|:----:|----------|---------------------|
| 是否需要重新搜索 | ✅ 需要 | ❌ **不需要** |
| 是否需要重新验价 | ✅ 需要 | ❌ **不需要** |
| 是否需要重新下单 | ✅ 需要 | ❌ **不需要** |
| 输入参数 | sessionId + passengers | orderNo（原订单号） |
| 输出 | 新 orderNo | 新 orderNo + pnrCode |

---

## 6. Post-Ticketing Baggage (出票后行李)

适用于订单已出票后，为已出票订单附加行李服务。

### 流程图

```
order.do ──→ pay.do ──→ (出票完成) ──→ postBookingAncillarySearch.do
                                                      │
                                                      ▼
                                               postBookingAncillaryOrder.do
                                                      │
                                                      ▼
                                               postBookingAncillaryPay.do
```

### 测试路线

| Airline | Route | Test Flow | Notes |
|---------|-------|-----------|-------|
| **SM (Air Cairo)** | **ELQ→HMB** | Order → Pay(出票) → **postBookingAncillarySearch** → **postBookingAncillaryOrder** → **postBookingAncillaryPay** | 出票后行李场景测试 |
| LS (Jet2) | STN→ALC | Order → Pay(出票) → Post-booking baggage | 备选路线 |

---

## 7. Refund (退款) Test Routes

### 流程图

```
queryOrderDetails.do (确认已出票) ──→ refundApply.do ──→ refundQuery.do
```

### 测试路线

| Airline | Route | Test Flow | Notes |
|---------|-------|-----------|-------|
| **7C (Jeju Air)** | **PUS→CJU** | Order → Pay → (出票确认) → **refundApply.do** → **refundQuery.do** | 退款流程测试推荐路线 |

---

## 8. Void (作废) Test Routes

### 流程图

```
queryOrderDetails.do (确认已出票) ──→ void.do
```

### 注意事项

- 作废操作有时间窗口限制（通常出票后特定小时内可操作）
- 作废后订单状态变为已取消，已出票的票证被作废

### 测试路线

| Airline | Route | Test Flow | Notes |
|---------|-------|-----------|-------|
| **7C (Jeju Air)** | **PUS→CJU** | Order → Pay → (出票确认) → **void.do** | 作废流程测试推荐路线 |

---

## 9. 完整 UAT 测试矩阵总览

| # | 测试场景 | 航司 | 航线 | 涉及接口 | 说明 |
|:-:|---------|------|------|---------|------|
| 1 | **联程预订** | 6E | AMS→MAA | search→verify→order→pay | 多段转机路由验证 |
| 2 | **直达预订** | (任选) | (任选) | search→verify→order→pay | 见上方直达替代路线 |
| 3 | **VCC 支付** | 7C | PUS→CJU | search→verify→order→pay(VCC) | 虚拟信用卡支付 |
| 4 | **行李(Inflow)** | IX | BOM→IXR | search→verify→getLuggage→order(含ancillaries)→pay | 基本航司行李选项 |
| 5 | **选座** | 6E | COK→DXB | search→verify→seatAvailability→order(含ancillaries)→pay | 座位选择和附加 |
| 6 | **支付超时重试** | 7C | PUS→CJU | order→pay(超时)→**regenerateOrder**→pay | 无需重新搜索验价下单 |
| 7 | **出票后行李** | SM | ELQ→HMB | order→pay→ticketed→**postBookingAncillarySearch→Order→Pay** | 售后行李加购 |
| 8 | **退款** | 7C | PUS→CJU | order→pay→ticketed→**refundApply→refundQuery** | 出票后退款 |
| 9 | **作废** | 7C | PUS→CJU | order→pay→ticketed→**void** | 出票后作废 |

---

## 10. Test Credentials

| Environment | Base URL | Notes |
|-------------|----------|-------|
| **Sandbox** | `https://sandbox.atriptech.com` | Sandbox credentials from ATRIP Portal; replace `<sandbox_secret>` with your actual secret |
| **Production** | Two URLs from ATRIP | One for search, another for other APIs |

> Sandbox credentials are generated at: ATRIP Portal → Profile → My Profile → Company Information

---

## 11. Testing Checklist by Scenario

### Full Booking (Flow A)
- [ ] search.do returns results with routingIdentifier
- [ ] verify.do returns valid sessionId
- [ ] getLuggage.do returns baggage options (if applicable)
- [ ] seatAvailability.do returns seat map (if applicable)
- [ ] order.do creates order successfully (returns orderNo)
- [ ] pay.do completes payment
- [ ] queryOrderDetails.do confirms ticketed status

### Get Offer Booker (Flow B)
- [ ] getOffers.do returns offerId
- [ ] getLuggage.do using offerId returns baggage options
- [ ] seatAvailability.do using offerId returns seat map
- [ ] order.do with offerId creates order
- [ ] pay.do completes payment

### FR Specific
- [ ] orderCommit.do succeeds between order and pay
- [ ] locale parameter correctly set

### UAT Extended Scenarios
- [ ] **Connecting flight**: 6E AMS→MAA multi-segment routing verified
- [ ] **VCC payment**: 7C PUS→CJU virtual credit card flow tested
- [ ] **Regenerate order**: Payment timeout → regenerateOrder.do → re-pay successful
- [ ] **Post-ticketing baggage**: SM ELQ→HMB → postBookingAncillarySearch/Order/Pay completed
- [ ] **Refund**: 7C PUS→CJU → refundApply → refundQuery completed
- [ ] **Void**: 7C PUS→CJU → void completed