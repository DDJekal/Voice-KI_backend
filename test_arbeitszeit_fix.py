import requests
import json
import time

# Konfiguration
API_URL = "https://voice-ki-backend.onrender.com/webhook/process-protocol"
WEBHOOK_SECRET = "8f15988e07ad5bef0a7050e91b7f3ebe"

# Protokoll mit "38-40 Wochenstunden" (der problematische Fall)
protocol = {
    "id": 64,
    "name": "Test 38-40 Wochenstunden",
    "pages": [
        {
            "id": 90,
            "name": "Der Bewerber erfüllt folgende Kriterien:",
            "position": 1,
            "prompts": [
                {"id": 313, "question": "zwingend: Studium Elektrotechnik", "position": 1},
                {"id": 311, "question": "Deutsch B2", "position": 2}
            ]
        },
        {
            "id": 91,
            "name": "Der Bewerber akzeptiert folgende Rahmenbedingungen:",
            "position": 2,
            "prompts": [
                {"id": 323, "question": "38-40 Wochenstunden", "position": 1}
            ]
        }
    ]
}

# Request vorbereiten
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {WEBHOOK_SECRET}"
}

body = protocol

# Request senden
print("=" * 70)
print("🧪 Testing arbeitszeit Union type fix")
print("=" * 70)
print(f"📄 Test Case: '38-40 Wochenstunden' (problematic string)")
print(f"⏱️  Start: {time.strftime('%H:%M:%S')}")
print("-" * 70)

start_time = time.time()

try:
    response = requests.post(
        API_URL,
        headers=headers,
        json=body,
        timeout=180
    )
    
    elapsed = time.time() - start_time
    
    print(f"⏱️  Ende: {time.strftime('%H:%M:%S')}")
    print(f"⚡ Dauer: {elapsed:.2f} Sekunden")
    print(f"📊 Status: {response.status_code}")
    print("-" * 70)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ ERFOLG! Union type fix funktioniert!")
        print(f"   📝 Fragen generiert: {len(result.get('questions', []))}")
    else:
        print(f"❌ FEHLER: {response.status_code}")
        print(f"   {response.text[:500]}")

except Exception as e:
    elapsed = time.time() - start_time
    print(f"❌ FEHLER nach {elapsed:.2f} Sekunden: {e}")

print("=" * 70)

