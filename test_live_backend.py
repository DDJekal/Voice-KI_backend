"""
Test Live Backend auf Render.com

Prüft ob das Backend deployed ist und korrekt antwortet.
"""

import requests
import json

# Test 1: Health Check
print("=" * 70)
print("TEST 1: Health Check")
print("=" * 70)

try:
    response = requests.get("https://voice-ki-backend.onrender.com/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 70)
print("TEST 2: Health Endpoint")
print("=" * 70)

try:
    response = requests.get("https://voice-ki-backend.onrender.com/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 70)
print("TEST 3: Webhook Test (Minimal Protocol)")
print("=" * 70)

# Minimales Test-Protokoll
test_protocol = {
    "id": 999,
    "name": "Test Protocol",
    "pages": [
        {
            "id": 1,
            "name": "Test Page",
            "position": 1,
            "prompts": [
                {
                    "id": 1,
                    "question": "zwingend: Test Qualifikation",
                    "position": 1
                }
            ]
        }
    ]
}

try:
    # Webhook Secret von .env holen (falls vorhanden)
    import os
    from pathlib import Path
    
    env_path = Path(".env")
    webhook_secret = None
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith("WEBHOOK_SECRET="):
                    webhook_secret = line.split("=", 1)[1].strip().strip('"')
                    break
    
    if not webhook_secret:
        print("WARNING: No WEBHOOK_SECRET found in .env")
        webhook_secret = "test-secret"
    
    headers = {
        "Authorization": f"Bearer {webhook_secret}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        "https://voice-ki-backend.onrender.com/webhook/process-protocol",
        json=test_protocol,
        headers=headers,
        timeout=60
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response Keys: {list(response.json().keys())}")
    print(f"\nFull Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # Check: Hat Response 'questions' Key?
    if 'questions' in response.json():
        print("\n[OK] Response has 'questions' key")
    else:
        print("\n[ERROR] Response is MISSING 'questions' key!")
        print("HOC will crash with KeyError!")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)

