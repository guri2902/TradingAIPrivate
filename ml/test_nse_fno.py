import requests
import json
from datetime import date


BASE_URL = "https://www.nseindia.com"

session = requests.Session()

headers = {
    "accept": "*/*",
    "accept-language": "en-IN,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "referer": "https://www.nseindia.com/report-detail/eq_security",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/144.0.0.0 Safari/537.36"
    ),
}


print("=" * 70)
print("DIRECT NSE F&O TEST")
print("=" * 70)


# ------------------------------------------------------------
# 1. Establish NSE session
# ------------------------------------------------------------

print("\nOpening NSE session...")

r = session.get(
    BASE_URL + "/report-detail/eq_security",
    headers=headers,
    timeout=20
)

print("Report page:", r.status_code)
print("Cookies:", len(session.cookies))


# ------------------------------------------------------------
# 2. Request F&O history
# ------------------------------------------------------------

params = {
    "symbol": "NIFTY",
    "from": "01-08-2026",
    "to": "17-08-2026",
    "expiryDate": "27-AUG-2026",
    "instrumentType": "FUTIDX",
    "year": "2026",
}

print("\nRequest parameters:")
for k, v in params.items():
    print(f"{k}: {v}")


url = BASE_URL + "/api/historicalOR/foCPV"

print("\nRequesting:")
print(url)

response = session.get(
    url,
    params=params,
    headers=headers,
    timeout=30
)

print("\nHTTP status:")
print(response.status_code)

print("\nContent-Type:")
print(response.headers.get("content-type"))

print("\nResponse size:")
print(len(response.content), "bytes")


print("\nFinal URL:")
print(response.url)


# ------------------------------------------------------------
# 3. Inspect response
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("RESPONSE")
print("=" * 70)

try:

    data = response.json()

    print(
        json.dumps(
            data,
            indent=2,
            default=str
        )[:20000]
    )

except Exception as e:

    print("Could not decode JSON:")
    print(e)

    print("\nFirst 5000 characters:")
    print(response.text[:5000])