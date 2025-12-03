"""
JWT Token Analyzer - Dekodiert den API Key um Expiry zu prüfen
"""

import base64
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('API_KEY')

if not api_key:
    print("❌ Kein API_KEY in .env gefunden")
    exit(1)

print("\n" + "="*70)
print("🔍 JWT Token Analyse")
print("="*70)

# JWT Format: header.payload.signature
parts = api_key.split('.')

if len(parts) != 3:
    print("❌ Ungültiges JWT Format")
    exit(1)

print(f"Token: {api_key[:30]}...")
print()

# Dekodiere Payload (mittlerer Teil)
try:
    # Füge Padding hinzu falls nötig
    payload_encoded = parts[1]
    padding = 4 - len(payload_encoded) % 4
    if padding != 4:
        payload_encoded += '=' * padding
    
    payload_decoded = base64.urlsafe_b64decode(payload_encoded)
    payload = json.loads(payload_decoded)
    
    print("📋 Token Payload:")
    print(json.dumps(payload, indent=2))
    print()
    
    # Prüfe Expiry
    if 'exp' in payload:
        exp_timestamp = payload['exp']
        exp_date = datetime.fromtimestamp(exp_timestamp)
        now = datetime.now()
        
        print(f"⏰ Ablauf-Datum:")
        print(f"   Token läuft ab: {exp_date.strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"   Aktuelles Datum: {now.strftime('%d.%m.%Y %H:%M:%S')}")
        print()
        
        if now > exp_date:
            days_expired = (now - exp_date).days
            print(f"❌ Token ist ABGELAUFEN seit {days_expired} Tagen!")
        else:
            days_valid = (exp_date - now).days
            print(f"✅ Token ist noch GÜLTIG für {days_valid} Tage")
    
    # Prüfe issued at
    if 'iat' in payload:
        iat_timestamp = payload['iat']
        iat_date = datetime.fromtimestamp(iat_timestamp)
        print(f"\n📅 Token erstellt am: {iat_date.strftime('%d.%m.%Y %H:%M:%S')}")
    
    # Tenant Info
    if 'tenant_name' in payload:
        print(f"\n🏢 Tenant: {payload['tenant_name']}")
    
except Exception as e:
    print(f"❌ Fehler beim Dekodieren: {e}")

print("\n" + "="*70)
print("💡 Wenn Token abgelaufen: Neuen Key im HOC Dashboard generieren")
print("="*70)

