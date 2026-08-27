# Atlas API UAT Verification Report
**Date of Execution:** 2026-08-27 11:16:56
**Environment:** Atlas Sandbox (`https://sandbox.atriptech.com`)
**Client ID:** `CTR12752_api_1`
**Overall UAT Status:** ✅ **PASSED (Ready for Production Go-Live Verification)**

---

## 📋 ATRIP Portal Verification Submission Table

Copy and paste these exact values into the corresponding fields in your ATRIP UAT Test dashboard:

| Test Scenario | Route | Date | `orderNo` | `pnrCode` | `sessionId` | `orderStatus` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Scenario 1 (Primary)** | `JKT` → `SUB` | `20260910` | `TESTA20260827111653610` | `P4X4Q9` | `a3f8bfd1-9132-4bd5-b1e1-787d536c8211` | `1` (Ticketed/InProcess) |
| **Scenario 2 (Secondary)** | `KUL` → `HGH` | `20260910` | `TESTA20260827111654910` | `EBR9EW` | `c1eb1162-4809-4489-a589-72ea9ec5e6c6` | `1` (Ticketed/InProcess) |

---

## 🔍 Detailed Evidence per Step

### Scenario 1 (JKT → SUB)
- **1.1 Search (`POST /search.do`)**: Status `0` | Routings: `34` | Price: `66.15 USD`
  - `routingIdentifier`: `SktUX1NVQl8xXzIwMjYwOTEwX18xXzBfMHxDVFIxMjc1Ml9hcGlfMXwxfDY2LjMwXzY2LjMwXzExLjIwXzAuMDBfMTQzLjgwX1VTRHxKS1RfU1VCXzFfMjAyNjA5MTBfXzFfMF8wXkNHSy1RRzcxNi0tU1VCLTIwMjYwOTEwMTUwNS0yMDI2MDkxMDE2NDUtRUNPLTEtXjY2LjMwXzY2LjMwXzExLjIwXzAuMDBfMTQzLjgwXkFRR19BUUdeXkFRRzFKS1RTVUI0MDAyMDI2MDkxMF5JRFJeMTE3MTIwNS4zMF4xMTcxMjA1LjMwXjE5Nzg3OS4wNF4xfDB8MjAyNjA4MjcxMTE2NTN8MHwxNzg3ODAwNjEzNDQyYmQ0MjM4MzB8fHx8fDAuMDB8M3wwfHxub3JtYWx8ZmFsc2V8MjAyNi0wOC0yNyAxMDo0NTo1Mnw=./xqkcUlWVInd7jcOsgDBnj/qQ4kGJPT55E/icP6QdpA=`
- **1.2 Verify (`POST /verify.do`)**: Status `0`
  - `sessionId`: `a3f8bfd1-9132-4bd5-b1e1-787d536c8211`
- **1.3 Order (`POST /order.do`)**: Status `0`
  - `orderNo`: `TESTA20260827111653610`
- **1.4 Pay (`POST /pay.do`)**: Status `0` | Result: `success`
- **1.5 Retrieve (`POST /queryOrderDetails.do`)**: Status `0`
  - `pnrCode`: `P4X4Q9` | Total: `66.3 USD`

### Scenario 2 (KUL → HGH)
- **2.1 Search (`POST /search.do`)**: Status `0` | Routings: `3` | Price: `63.58 USD`
  - `routingIdentifier`: `S1VMX0hHSF8xXzIwMjYwOTEwX18xXzBfMHxDVFIxMjc1Ml9hcGlfMXwxfDgxLjM1XzgxLjM1XzgyLjAxXzAuMDBfMjQ0LjcxX1VTRHxLVUxfSEdIXzFfMjAyNjA5MTBfXzFfMF8wXktVTC1UUjQ1Ny1YLVNJTi0yMDI2MDkxMDA3MDUtMjAyNjA5MTAwODMwLUZseS0xLSNTSU4tVFIxODgtWC1IR0gtMjAyNjA5MTAxNjMwLTIwMjYwOTEwMjE0NS1GbHktMS1eODEuMzVfODEuMzVfODIuMDFfMC4wMF8yNDQuNzFeQVRSTkRDX0FUUk5EQ15eQVRSTkRDMUtVTEhHSDIwMDIwMjYwOTEwXk1ZUl4zMjYuNzJeMzI2LjcyXjMyOS4zN14xfDF8MjAyNjA4MjcxMTE2NTR8MHwxNzg3ODAwNjE0Nzc1ZWQyNjk1Njd8fHx8fDAuMDB8M3wwfHxub3JtYWx8ZmFsc2V8MjAyNi0wOC0yNyAxMDowMjowMXw=.D+T0AeYuaXnRzUf/+B6/xMmAbQgwlPUh89KUOeA1beg=`
- **2.2 Verify (`POST /verify.do`)**: Status `0`
  - `sessionId`: `c1eb1162-4809-4489-a589-72ea9ec5e6c6`
- **2.3 Order (`POST /order.do`)**: Status `0`
  - `orderNo`: `TESTA20260827111654910`
- **2.4 Pay (`POST /pay.do`)**: Status `0` | Result: `success`
- **2.5 Retrieve (`POST /queryOrderDetails.do`)**: Status `0`
  - `pnrCode`: `EBR9EW` | Total: `81.35 USD`

---

## ✅ Pre-Launch Readiness Checklist
- [x] Correct UAT Process selected (**Search and Ticketing UAT / 机票预订**)
- [x] Standard Request Headers sent (`Content-Type: application/json`, `Accept: */*`, `Accept-Encoding: gzip`)
- [x] Status code validated (`status === 0`)
- [x] Traceable `orderNo`, `sessionId`, `routingIdentifier`, `pnrCode` captured
- [x] End-to-end booking flow successfully verified on Sandbox
