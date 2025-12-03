"""
Detaillierte API Diagnose - Testet verschiedene Authentifizierungs-Methoden
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_url = os.getenv('API_URL', 'https://high-office.hirings.cloud/api/v1')
api_key = os.getenv('API_KEY')

print("\n" + "="*70)
print("🔬 Detaillierte API Diagnose")
print("="*70)
print(f"API Base URL: {api_url}")
print(f"API Key: {api_key[:40]}..." if api_key else "❌ Kein Key")
print("="*70 + "\n")

# Test verschiedene Auth-Methoden
auth_methods = [
    ("Direct Token (kein Bearer)", {'Authorization': f'{api_key}'}),
    ("Bearer Token (Standard)", {'Authorization': f'Bearer {api_key}'}),
    ("JWT Token", {'Authorization': f'JWT {api_key}'}),
    ("Token Header", {'Token': api_key}),
    ("X-API-Key Header", {'X-API-Key': api_key}),
]

endpoint = f"{api_url}/applicants/new"

print(f"🎯 Teste Endpoint: {endpoint}")
print("="*70 + "\n")

for method_name, headers in auth_methods:
    print(f"🧪 Teste: {method_name}")
    print(f"   Headers: {list(headers.keys())}")
    
    try:
        response = requests.get(endpoint, headers=headers, timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ ERFOLG!")
            data = response.json()
            print(f"   Response Keys: {list(data.keys())[:5]}")
            break
        elif response.status_code == 401:
            print(f"   ❌ Unauthorized")
            # Zeige Response Body für mehr Info
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error Text: {response.text[:100]}")
        else:
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
    
    print()

print("="*70)
print("📝 Empfehlung:")
print("   1. Prüfe HOC Dashboard → API Keys → Permissions")
print("   2. Prüfe ob Key für '/applicants' Endpoint aktiviert ist")
print("   3. Kontaktiere HOC Support für korrekte Auth-Methode")
print("="*70)

