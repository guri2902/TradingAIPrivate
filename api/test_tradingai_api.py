# ============================================================
# TradingAI - API TEST
# ============================================================

from fastapi.testclient import (
    TestClient,
)

from api.tradingai_api import app


client = TestClient(
    app
)


print("=" * 70)
print(
    "TradingAI - API TEST"
)
print("=" * 70)


# ============================================================
# TEST 1 - HEALTH
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - HEALTH")
print("=" * 70)

response = client.get(
    "/health"
)

print(
    "Status:",
    response.status_code
)

print(
    response.json()
)

if response.status_code != 200:

    raise RuntimeError(
        "Health endpoint failed."
    )


# ============================================================
# TEST 2 - ROOT
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - ROOT")
print("=" * 70)

response = client.get(
    "/"
)

print(
    response.json()
)

if response.status_code != 200:

    raise RuntimeError(
        "Root endpoint failed."
    )


# ============================================================
# TEST 3 - NIFTY MARKET STATE
# ============================================================

print("\n" + "=" * 70)
print(
    "TEST 3 - NIFTY MARKET STATE"
)
print("=" * 70)

response = client.get(
    "/v1/market/NIFTY"
)

print(
    "Status:",
    response.status_code
)

if response.status_code != 200:

    print(
        response.text
    )

    raise RuntimeError(
        "NIFTY market endpoint failed."
    )

payload = (
    response.json()
)

data = (
    payload[
        "data"
    ]
)

print(
    "Current:",
    data[
        "current"
    ]
)

print(
    "Options:",
    data[
        "options"
    ]
)

print(
    "Futures:",
    data[
        "futures"
    ]
)

print(
    "Freshness:",
    data[
        "freshness"
    ]
)


required = [
    "instrument",
    "current",
    "market",
    "options",
    "futures",
    "freshness",
]

missing = [
    key
    for key in required
    if key not in data
]

if missing:

    raise RuntimeError(
        f"Missing API state fields: "
        f"{missing}"
    )


# ============================================================
# TEST 4 - RISK
# ============================================================

print("\n" + "=" * 70)
print(
    "TEST 4 - RISK"
)
print("=" * 70)

response = client.get(
    "/v1/risk/check",
    params={
        "side": "LONG",
        "entry": 100,
        "stop_loss": 98,
        "target": 104,
    },
)

print(
    "Status:",
    response.status_code
)

print(
    response.json()
)

if response.status_code != 200:

    raise RuntimeError(
        "Risk endpoint failed."
    )


risk_data = (
    response.json()[
        "data"
    ]
)

if "allowed" not in risk_data:

    raise RuntimeError(
        "Risk response missing "
        "'allowed'."
    )


# ============================================================
# TEST 5 - COMBINED ENDPOINT
# ============================================================

print("\n" + "=" * 70)
print(
    "TEST 5 - COMBINED TRADINGAI"
)
print("=" * 70)

response = client.get(
    "/v1/tradingai/NIFTY"
)

print(
    "Status:",
    response.status_code
)

if response.status_code != 200:

    print(
        response.text
    )

    raise RuntimeError(
        "Combined TradingAI endpoint failed."
    )

combined = (
    response.json()[
        "data"
    ]
)

print(
    "Current:",
    combined[
        "current"
    ]
)

print(
    "Freshness:",
    combined[
        "freshness"
    ]
)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print(
    "TRADINGAI API TEST PASSED"
)
print("=" * 70)