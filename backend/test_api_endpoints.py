"""
Alternative API Endpoint Tests

Probiert verschiedene Endpoints aus um herauszufinden welcher funktioniert.
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_url = os.getenv('API_URL', 'https://high-office.hirings.cloud/api/v1')
api_key = os.getenv('API_KEY')

print("\n" + "="*70)
print("🧪 Teste verschiedene API Endpoints")
print("="*70)
print(f"API URL: {api_url}")
print(f"API Key: {api_key[:30]}..." if api_key else "❌ Kein Key")
print("="*70 + "\n")

# Test verschiedene Endpoints
endpoints = [
    "/applicants/new",
    "/applicants?status=new",
    "/campaigns",
    "/campaigns/16",
    "/health",
    "/status",
]

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

for endpoint in endpoints:
    url = f"{api_url}{endpoint}"
    print(f"📡 Teste: {endpoint}")
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Erfolgreich! Keys: {list(data.keys())[:5]}")
            
            # Zeige Campaign-Struktur
            if 'campaigns' in data:
                campaigns = data['campaigns']
                print(f"   Campaigns gefunden: {len(campaigns)}")
                if campaigns:
                    print(f"   Erste Campaign ID: {campaigns[0].get('id')}")
        elif response.status_code == 401:
            print(f"   ❌ Unauthorized")
        elif response.status_code == 404:
            print(f"   ⚠️  Not Found")
        else:
            print(f"   ⚠️  {response.status_code}: {response.text[:100]}")
            
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
    
    print()

print("="*70)
print("💡 Wenn alle Endpoints 401 geben, ist der API-Key ungültig")
print("="*70)

