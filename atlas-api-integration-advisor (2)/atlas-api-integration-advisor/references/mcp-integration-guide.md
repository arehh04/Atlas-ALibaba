# MCP Integration Guide

This reference describes how to use the GitBook MCP service to look up precise API documentation when needed.

---

## MCP Service Details

| Property | Value |
|----------|-------|
| **URL** | `https://resources.atriptech.com/~gitbook/mcp` |
| **Protocol** | JSON-RPC over SSE |
| **Available Tools** | `searchDocumentation`, `getPage` |

---

## When to Use MCP vs When to Use Skill Knowledge

| Use Case | Source |
|----------|--------|
| Client asks: "How do I book a flight?" | **Skill knowledge** (flow guidance) |
| Client asks: "What does `refundStatus=T` mean?" | **MCP** (exact field definition) |
| Client asks: "Which flow should I use?" | **Skill knowledge** (scenario decision) |
| Client asks: "Can you show me the schema for seatAvailability.do?" | **MCP** (`getPage`) |
| Client asks: "Generate Python code for booking flow" | **Skill knowledge** (code generation) |
| Client encounters status code 320 on order.do | **MCP** (error code lookup) |
| Client asks: "Does seatAvailability still support independent mode?" | **MCP** (check latest update notes) |

---

## Tool Usage

### searchDocumentation

Search the Atlas API documentation by keyword.

```json
{
    "query": "<search keyword>"
}
```

**Best practice:** Use specific terms — endpoint names, field names, or error codes.
Examples:
- `"seatAvailability.do"`
- `"refundStatus"`
- `"refundRules"`
- `"Error Codes"`
- `"order.do contact"`

### getPage

Get full content of a specific documentation page by URL.

```json
{
    "pageUrl": "https://resources.atriptech.com/api-document/api-reference/booking-apis/search"
}
```

**Best practice:** When `searchDocumentation` returns a relevant page link, use `getPage` to fetch the complete endpoint schema with all field definitions.

---

## Integration Pattern

```
Client Question
      │
      ▼
Does the skill knowledge cover this?
      │
      ├── YES → Answer from skill guidance
      │
      └── NO → Trigger MCP lookup:
                searchDocumentation("<keyword>")
                      │
                      ▼
                getPage("<best matching URL>")
                      │
                      ▼
                Extract schema/field info
                Combine with skill context
                      │
                      ▼
                Answer the client
```

---

## Important Notes

- The MCP service provides the **latest** documentation — always prefer it for field-level details
- The MCP may return incomplete responses if the documentation page has collapsed sections (e.g., expandable "Show properties" elements)
- For complex questions, use multiple searches with different keywords
- Always combine MCP results with the skill's integration context