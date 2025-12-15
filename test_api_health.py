"""
Einfacher API Health Check
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://voice-ki-backend.onrender.com"
API_KEY = os.getenv("API_KEY")

# Test 1: Health Check
print("=" * 60)
print("API Health Check")
print("=" * 60)

try:
    response = requests.get(f"{API_URL}/health", timeout=10)
    print(f"Health Endpoint: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
except Exception as e:
    print(f"Health Check Error: {e}")

# Test 2: Process Protocol Endpoint
print("\n" + "=" * 60)
print("Process Protocol Endpoint Check")
print("=" * 60)

test_data = {
    "sections": [
        {
            "page_id": 1,
            "role": "assistant",
            "content": "Haben Sie Führerschein Klasse B?"
        },
        {
            "page_id": 2,
            "role": "user",
            "content": "Ja"
        }
    ]
}

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

try:
    response = requests.post(
        f"{API_URL}/api/process-protocol",
        headers=headers,
        json=test_data,
        timeout=30
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

