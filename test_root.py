#!/usr/bin/env python3
"""Test root endpoint"""

import requests

url = "http://localhost:8000/"
response = requests.get(url)

print(f"Status Code: {response.status_code}")
print(f"Content-Type: {response.headers.get('content-type')}")
print(f"Content Length: {len(response.text)}")
print(f"\nFirst 300 chars:\n{response.text[:300]}")

if response.text.startswith("<!DOCTYPE"):
    print("\n✓ HTML wird korrekt zurückgegeben!")
elif response.text.startswith("{"):
    print("\n✗ JSON wird zurückgegeben statt HTML")
else:
    print("\n? Unbekanntes Format")
