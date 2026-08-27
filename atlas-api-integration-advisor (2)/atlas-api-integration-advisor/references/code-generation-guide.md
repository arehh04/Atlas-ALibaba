# Code Generation Guide

Guidelines for generating integration code in different programming languages for clients.

> 📖 **For complete ancillary service guidance (request/response schemas, error handling, data chaining), see SKILL.md §8b — Ancillary Services.**

---

## General Principles

1. **Always determine the client's language** before generating code
2. **Use sandbox credentials and base URL** in example code
3. **Show the complete flow** — not just individual API calls
4. **Include error handling** for common status codes
5. **Use comments** to explain data chaining between steps
6. **Add environment switch** comments (sandbox vs production)

---
## ⚠️ Environment URLs — Search and Transaction APIs Must Use Different Domains

All code templates use the sandbox URL `https://sandbox.atriptech.com`. In production, **search and transaction URLs must use different domains** — do not mix them.

**Sandbox environment:** A single URL works for all APIs
```python
BASE_URL = "https://sandbox.atriptech.com"   # Both search and transaction APIs
```

**Production environment (replace with actual URLs from ATRIP Portal):**

| Client Type | Search URL | Transaction URL (verify/order/pay/post-booking etc.) |
|:-----------|:-----------|:-----------------------------------------------------|
| 🇨🇳 China clients | `https://search.yutu-api.com` | `https://api.yutu-api.com` |
| 🌍 International clients | `https://api.atriptech.com/search` | `https://api.atriptech.com` |

```python
# Production example (China client)
SEARCH_BASE_URL = "https://search.yutu-api.com"           # search.do only
TRANSACTION_BASE_URL = "https://api.yutu-api.com"          # verify/order/pay/refund/void/post-booking

# Usage:
# search.do → SEARCH_BASE_URL
# All other endpoints → TRANSACTION_BASE_URL
```

> ⚠️ **Critical rule:** Never use the same base URL for `search.do` and transaction APIs in production. Always verify with ATRIP → Profile → My Profile → Company Information.

---

## Python Template

```python
import requests
import json
import time
import logging

# === CONFIGURATION ===
BASE_URL = "https://sandbox.atriptech.com"
CLIENT_ID = "<your_client_id>"
CLIENT_SECRET = "<your_client_secret>"
MAX_RETRIES = 5

# Transient errors that can be retried
TRANSIENT_ERRORS = {112, 113, 205, 316}

headers = {
    "Content-Type": "application/json",
    "x-atlas-client-id": CLIENT_ID,
    "x-atlas-client-secret": CLIENT_SECRET,
    "Accept": "application/json"
}

# For search.do only, add:
# headers["Accept-Encoding"] = "gzip"

def call_api_with_retry(endpoint, body, extra_headers=None):
    """Call API with exponential backoff retry for transient errors."""
    api_headers = {**headers, **(extra_headers or {})}
    
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(f"{BASE_URL}{endpoint}", headers=api_headers, json=body, timeout=30)
            data = resp.json()
        except requests.exceptions.Timeout:
            logging.warning(f"Timeout on {endpoint}, attempt {attempt + 1}")
            wait = min(2 ** attempt, 15)
            time.sleep(wait)
            continue
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed on {endpoint}: {e}")
            raise

        if data.get("status") == 0:
            return data

        if data.get("status") in TRANSIENT_ERRORS:
            logging.warning(f"Transient error {data['status']} on {endpoint}, "
                          f"attempt {attempt + 1}/{MAX_RETRIES}")
            wait = min(2 ** attempt, 15)
            time.sleep(wait)
            continue

        # Non-transient error — raise immediately
        raise Exception(f"API error {data['status']}: {data.get('msg', '')} "
                       f"on {endpoint}")
    
    raise Exception(f"Max retries ({MAX_RETRIES}) exceeded for {endpoint}")

def booking_flow_a():
    """Flow A: Search → Verify → Order → Pay"""

    # Step 1: Search (with retry)
    search_body = {
        "tripType": "1",
        "adultNum": 1,
        "childNum": 0,
        "infantNum": 0,
        "fromCity": "STN",
        "toCity": "ALC",
        "fromDate": "20261018",
        "airlines": ["LS"]
    }

    data = call_api_with_retry("/search.do", search_body,
                                extra_headers={"Accept-Encoding": "gzip"})
    if data["status"] != 0:
        raise Exception(f"Search failed: {data}")

    routing = data["routings"][0]
    routing_id = routing["routingIdentifier"]

    # Step 2: Verify (with retry)
    verify_body = {"routingIdentifier": routing_id}
    verify_data = call_api_with_retry("/verify.do", verify_body)
    if verify_data["status"] != 0:
        raise Exception(f"Verify failed: {verify_data}")

    session_id = verify_data["sessionId"]

    # Step 3 [Optional]: Get Luggage
    luggage_body = {"offerId": session_id}
    luggage_data = call_api_with_retry("/getLuggage.do", luggage_body)
    # luggage_options = resp.json()
    # Select product codes from luggage_options

    # Step 4 [Optional]: Seat Availability
    # seat_body = {
    #     "sessionId": session_id,
    #     "carrier": "LS",
    #     "outboundSegments": [{
    #         "flightNumber": "LS1411",
    #         "segmentIndex": 1,
    #         "depAirport": "STN",
    #         "arrAirport": "ALC",
    #         "cabinClass": "1",
    #         "depTime": "202610180835"
    #     }]
    # }
    # resp = requests.post(f"{BASE_URL}/seatAvailability.do", headers=headers, json=seat_body)

    # Step 5: Create Order
    order_body = {
        "sessionId": session_id,
        "passengers": [{
            "name": "Testpass/Example",
            "passengerType": 0,
            "birthday": "19900101",
            "gender": "M",
            "nationality": "GB",
            "ancillaries": []
        }],
        "contact": {
            "name": "Testpass/Example",
            "email": "test@example.com",
            "mobile": "0044-71234567890"
        }
    }

    resp = call_api_with_retry("/order.do", order_body)
    order_data = resp
    if order_data["status"] != 0:
        raise Exception(f"Order failed: {order_data}")

    order_no = order_data["orderNo"]
    print(f"Order created: {order_no}")

    # Step 6 [FR only]: orderCommit.do
    # if carrier == "FR":
    #     resp = requests.post(f"{BASE_URL}/orderCommit.do",
    #         headers=headers, json={"orderNo": order_no})

    # Step 7: Pay
    pay_body = {
        "orderNo": order_no,
        "paymentMethod": 1
    }

    pay_data = call_api_with_retry("/pay.do", pay_body)
    print(f"Payment result: {pay_data['status']}")

    # Step 8: Query Order Status
    order_details = call_api_with_retry("/queryOrderDetails.do",
                                          {"orderNo": order_no})
    print(f"Order status: {order_details.get('orderStatus')}")
    print(f"Ticket status: {order_details.get('ticketStatus')}")

    return order_no


def booking_flow_b():
    """Flow B: GetOffer → Order → Pay"""

    # Step 1: Get Offer
    offer_body = {
        # Structure depends on known itinerary
    }
    # resp = requests.post(f"{BASE_URL}/getOffers.do", headers=headers, json=offer_body)
    # offer_id = resp.json()["offerId"]

    # Step 2: Order (using offerId)
    # order_body = {
    #     "offerId": offer_id,
    #     "passengers": [...],
    #     "contact": {...}
    # }

    # Step 3: Pay
    pass


if __name__ == "__main__":
    booking_flow_a()
```

---

## PHP Template

```php
<?php
$baseUrl = "https://sandbox.atriptech.com";
$clientId = "<your_client_id>";
$clientSecret = "<your_client_secret>";

$headers = [
    "Content-Type: application/json",
    "x-atlas-client-id: $clientId",
    "x-atlas-client-secret: $clientSecret",
    "Accept: application/json"
];

function callApi($url, $body, $extraHeaders = []) {
    global $headers;
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($body));
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, array_merge($headers, $extraHeaders));
    $response = curl_exec($ch);
    curl_close($ch);
    return json_decode($response, true);
}

// Step 1: Search
$searchBody = [
    "tripType" => "1",
    "adultNum" => 1,
    "fromCity" => "STN",
    "toCity" => "ALC",
    "fromDate" => "20261018",
    "airlines" => ["LS"]
];
$searchResult = callApi(
    "$baseUrl/search.do",
    $searchBody,
    ["Accept-Encoding: gzip"]
);

$routingId = $searchResult['routings'][0]['routingIdentifier'];

// Step 2: Verify
$verifyResult = callApi("$baseUrl/verify.do", [
    "routingIdentifier" => $routingId
]);
$sessionId = $verifyResult['sessionId'];

// Step 3: Order
$orderResult = callApi("$baseUrl/order.do", [
    "sessionId" => $sessionId,
    "passengers" => [[
        "name" => "Testpass/Example",
        "passengerType" => 0,
        "birthday" => "19900101",
        "gender" => "M",
        "nationality" => "GB"
    ]],
    "contact" => [
        "name" => "Testpass/Example",
        "email" => "test@example.com",
        "mobile" => "0044-71234567890"
    ]
]);

// Step 4: Pay
$payResult = callApi("$baseUrl/pay.do", [
    "orderNo" => $orderResult['orderNo'],
    "paymentMethod" => 1
]);

echo "Order: " . $orderResult['orderNo'] . "\n";
echo "Payment: " . $payResult['status'] . "\n";
?>
```

---

## Java Template

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import com.google.gson.*;

public class AtlasBookingFlow {

    static final String BASE_URL = "https://sandbox.atriptech.com";
    static final String CLIENT_ID = "<your_client_id>";
    static final String CLIENT_SECRET = "<your_client_secret>";

    static HttpClient client = HttpClient.newHttpClient();
    static Gson gson = new Gson();

    static JsonObject callApi(String endpoint, JsonObject body, boolean gzipEncoding) throws Exception {
        String url = BASE_URL + endpoint;
        HttpRequest.Builder builder = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .header("Content-Type", "application/json")
            .header("x-atlas-client-id", CLIENT_ID)
            .header("x-atlas-client-secret", CLIENT_SECRET)
            .header("Accept", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(body.toString()));

        if (gzipEncoding) {
            builder.header("Accept-Encoding", "gzip");
        }

        HttpResponse<String> response = client.send(builder.build(),
            HttpResponse.BodyHandlers.ofString());

        return gson.fromJson(response.body(), JsonObject.class);
    }

    public static void main(String[] args) throws Exception {
        // Step 1: Search
        JsonObject searchBody = new JsonObject();
        searchBody.addProperty("tripType", "1");
        searchBody.addProperty("adultNum", 1);
        searchBody.addProperty("fromCity", "STN");
        searchBody.addProperty("toCity", "ALC");
        searchBody.addProperty("fromDate", "20261018");

        JsonObject searchResult = callApi("/search.do", searchBody, true);
        String routingId = searchResult.getAsJsonArray("routings")
            .get(0).getAsJsonObject()
            .get("routingIdentifier").getAsString();

        // Step 2: Verify
        JsonObject verifyBody = new JsonObject();
        verifyBody.addProperty("routingIdentifier", routingId);
        JsonObject verifyResult = callApi("/verify.do", verifyBody, false);
        String sessionId = verifyResult.get("sessionId").getAsString();

        // Step 3: Order
        JsonObject passenger = new JsonObject();
        passenger.addProperty("name", "Testpass/Example");
        passenger.addProperty("passengerType", 0);
        passenger.addProperty("birthday", "19900101");
        passenger.addProperty("gender", "M");
        passenger.addProperty("nationality", "GB");

        JsonObject contact = new JsonObject();
        contact.addProperty("name", "Testpass/Example");
        contact.addProperty("email", "test@example.com");
        contact.addProperty("mobile", "0044-71234567890");

        JsonObject orderBody = new JsonObject();
        orderBody.addProperty("sessionId", sessionId);

        JsonArray passengers = new JsonArray();
        passengers.add(passenger);
        orderBody.add("passengers", passengers);
        orderBody.add("contact", contact);

        JsonObject orderResult = callApi("/order.do", orderBody, false);
        String orderNo = orderResult.get("orderNo").getAsString();

        // Step 4: Pay
        JsonObject payBody = new JsonObject();
        payBody.addProperty("orderNo", orderNo);
        payBody.addProperty("paymentMethod", 1);

        JsonObject payResult = callApi("/pay.do", payBody, false);
        System.out.println("Order: " + orderNo);
        System.out.println("Payment status: " + payResult.get("status"));
    }
}
```

---

## Node.js Template

```javascript
const axios = require('axios');

const BASE_URL = 'https://sandbox.atriptech.com';
const CLIENT_ID = '<your_client_id>';
const CLIENT_SECRET = '<your_client_secret>';

const headers = {
  'Content-Type': 'application/json',
  'x-atlas-client-id': CLIENT_ID,
  'x-atlas-client-secret': CLIENT_SECRET,
  'Accept': 'application/json'
};

async function bookingFlowA() {
  // Step 1: Search
  const searchResp = await axios.post(`${BASE_URL}/search.do`, {
    tripType: '1',
    adultNum: 1,
    fromCity: 'STN',
    toCity: 'ALC',
    fromDate: '20261018',
    airlines: ['LS']
  }, { headers: { ...headers, 'Accept-Encoding': 'gzip' } });

  const routingId = searchResp.data.routings[0].routingIdentifier;

  // Step 2: Verify
  const verifyResp = await axios.post(`${BASE_URL}/verify.do`, {
    routingIdentifier: routingId
  }, { headers });

  const sessionId = verifyResp.data.sessionId;

  // Step 3: Order
  const orderResp = await axios.post(`${BASE_URL}/order.do`, {
    sessionId,
    passengers: [{
      name: 'Testpass/Example',
      passengerType: 0,
      birthday: '19900101',
      gender: 'M',
      nationality: 'GB',
      ancillaries: []
    }],
    contact: {
      name: 'Testpass/Example',
      email: 'test@example.com',
      mobile: '0044-71234567890'
    }
  }, { headers });

  const orderNo = orderResp.data.orderNo;

  // Step 4: Pay
  const payResp = await axios.post(`${BASE_URL}/pay.do`, {
    orderNo,
    paymentMethod: 1
  }, { headers });

  console.log(`Order: ${orderNo}`);
  console.log(`Payment status: ${payResp.data.status}`);
  return orderNo;
}

bookingFlowA().catch(console.error);
```

---

## Go Template

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
)

const (
    baseURL    = "https://sandbox.atriptech.com"
    clientID   = "<your_client_id>"
    clientSecret = "<your_client_secret>"
)

func callAPI(endpoint string, body interface{}, gzip bool) (map[string]interface{}, error) {
    jsonBody, _ := json.Marshal(body)
    req, _ := http.NewRequest("POST", baseURL+endpoint, bytes.NewBuffer(jsonBody))
    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("x-atlas-client-id", clientID)
    req.Header.Set("x-atlas-client-secret", clientSecret)
    req.Header.Set("Accept", "application/json")
    if gzip {
        req.Header.Set("Accept-Encoding", "gzip")
    }

    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    respBody, _ := io.ReadAll(resp.Body)
    var result map[string]interface{}
    json.Unmarshal(respBody, &result)
    return result, nil
}

func main() {
    // Step 1: Search
    searchBody := map[string]interface{}{
        "tripType": "1",
        "adultNum": 1,
        "fromCity": "STN",
        "toCity":  "ALC",
        "fromDate": "20261018",
        "airlines": []string{"LS"},
    }

    searchResp, _ := callAPI("/search.do", searchBody, true)
    routings := searchResp["routings"].([]interface{})
    routing := routings[0].(map[string]interface{})
    routingId := routing["routingIdentifier"].(string)

    // Step 2: Verify
    verifyResp, _ := callAPI("/verify.do", map[string]interface{}{
        "routingIdentifier": routingId,
    }, false)
    sessionId := verifyResp["sessionId"].(string)

    // Step 3: Order
    orderResp, _ := callAPI("/order.do", map[string]interface{}{
        "sessionId": sessionId,
        "passengers": []interface{}{
            map[string]interface{}{
                "name": "Testpass/Example",
                "passengerType": 0,
                "birthday": "19900101",
                "gender": "M",
                "nationality": "GB",
            },
        },
        "contact": map[string]interface{}{
            "name": "Testpass/Example",
            "email": "test@example.com",
            "mobile": "0044-71234567890",
        },
    }, false)

    orderNo := orderResp["orderNo"].(string)

    // Step 4: Pay
    payResp, _ := callAPI("/pay.do", map[string]interface{}{
        "orderNo": orderNo,
        "paymentMethod": 1,
    }, false)

    fmt.Printf("Order: %s\n", orderNo)
    fmt.Printf("Payment status: %.0f\n", payResp["status"])
}
```

---

## C# Template

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

public class AtlasBookingFlow
{
    private static readonly string BaseUrl = "https://sandbox.atriptech.com";
    private static readonly string ClientId = "<your_client_id>";
    private static readonly string ClientSecret = "<your_client_secret>";
    private static readonly HttpClient HttpClient = new HttpClient();

    public AtlasBookingFlow()
    {
        HttpClient.DefaultRequestHeaders.Add("Content-Type", "application/json");
        HttpClient.DefaultRequestHeaders.Add("x-atlas-client-id", ClientId);
        HttpClient.DefaultRequestHeaders.Add("x-atlas-client-secret", ClientSecret);
        HttpClient.DefaultRequestHeaders.Add("Accept", "application/json");
    }

    private async Task<JsonDocument> CallApiAsync(string endpoint, object body, bool gzip = false)
    {
        var jsonBody = JsonSerializer.Serialize(body);
        var content = new StringContent(jsonBody, Encoding.UTF8, "application/json");

        if (gzip)
        {
            HttpClient.DefaultRequestHeaders.Remove("Accept-Encoding");
            HttpClient.DefaultRequestHeaders.Add("Accept-Encoding", "gzip");
        }

        var response = await HttpClient.PostAsync($"{BaseUrl}{endpoint}", content);
        var responseBody = await response.Content.ReadAsStringAsync();
        return JsonDocument.Parse(responseBody);
    }

    public async Task<string> BookingFlowAAsync()
    {
        // Step 1: Search
        var searchBody = new
        {
            tripType = "1",
            adultNum = 1,
            childNum = 0,
            infantNum = 0,
            fromCity = "STN",
            toCity = "ALC",
            fromDate = "20261018",
            airlines = new[] { "LS" }
        };

        var searchResult = await CallApiAsync("/search.do", searchBody, gzip: true);
        var routingId = searchResult.RootElement
            .GetProperty("routings")[0]
            .GetProperty("routingIdentifier")
            .GetString();

        // Step 2: Verify
        var verifyResult = await CallApiAsync("/verify.do", new
        {
            routingIdentifier = routingId
        });
        var sessionId = verifyResult.RootElement
            .GetProperty("sessionId")
            .GetString();

        // Step 3: Create Order
        var orderResult = await CallApiAsync("/order.do", new
        {
            sessionId = sessionId,
            passengers = new[]
            {
                new
                {
                    name = "Testpass/Example",
                    passengerType = 0,
                    birthday = "19900101",
                    gender = "M",
                    nationality = "GB",
                    ancillaries = Array.Empty<object>()
                }
            },
            contact = new
            {
                name = "Testpass/Example",
                email = "test@example.com",
                mobile = "0044-71234567890"
            }
        });

        var orderNo = orderResult.RootElement
            .GetProperty("orderNo")
            .GetString();

        // Step 4: Pay
        var payResult = await CallApiAsync("/pay.do", new
        {
            orderNo = orderNo,
            paymentMethod = 1
        });

        Console.WriteLine($"Order: {orderNo}");
        Console.WriteLine($"Payment status: {payResult.RootElement.GetProperty("status")}");

        return orderNo;
    }

    public static async Task Main(string[] args)
    {
        var flow = new AtlasBookingFlow();
        await flow.BookingFlowAAsync();
    }
}
```

---

## Language-Specific Notes

| Language | JSON Library | HTTP Client | Notes |
|----------|-------------|-------------|-------|
| **Python** | built-in `json` | `requests` | Simple, widely used. Add `requests` to requirements.txt |
| **PHP** | `json_encode`/`json_decode` | `curl` | Built-in JSON support. Use `curl` for HTTP |
| **Java** | `Gson` or `Jackson` | `java.net.http.HttpClient` (Java 11+) | Add Gson/Jackson dependency |
| **Node.js** | built-in `JSON` | `axios` or `fetch` | Add axios to package.json |
| **Go** | `encoding/json` | `net/http` | Standard library only, no external deps |
| **C#** | `Newtonsoft.Json` or `System.Text.Json` | `HttpClient` | Add NuGet package |

When generating code for a specific client, use the appropriate template above as a starting point and adapt for their specific scenario (Flow A vs Flow B, with/without ancillaries, etc.).