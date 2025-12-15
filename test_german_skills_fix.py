import requests
import json
import time

# Konfiguration
API_URL = "https://voice-ki-backend.onrender.com/webhook/process-protocol"
WEBHOOK_SECRET = "8f15988e07ad5bef0a7050e91b7f3ebe"

# Protokoll mit Deutschkenntnissen in Qualifikationen (der problematische Fall)
protocol = {
    "id": 65,
    "name": "Test Deutschkenntnisse separat",
    "pages": [
        {
            "id": 90,
            "name": "Der Bewerber erfüllt folgende Kriterien:",
            "position": 1,
            "prompts": [
                {"id": 313, "question": "zwingend: Studium Informatik", "position": 1},
                {"id": 315, "question": "alternativ: Ausbildung zum Fachinformatiker", "position": 2},
                {"id": 317, "question": "alternativ: IT-Zertifizierung", "position": 3},
                {"id": 311, "question": "Deutschkenntnisse B2", "position": 4}
            ]
        },
        {
            "id": 91,
            "name": "Der Bewerber akzeptiert folgende Rahmenbedingungen:",
            "position": 2,
            "prompts": [
                {"id": 323, "question": "Vollzeit", "position": 1}
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
print("🧪 Testing German Language Skills Separation Fix")
print("=" * 70)
print(f"📄 Test Case: Deutschkenntnisse sollten NICHT in Abschluss-Frage sein")
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
        questions = result.get('questions', [])
        
        print("✅ ERFOLG!")
        print(f"   📝 Fragen generiert: {len(questions)}")
        print()
        
        # Prüfe ob es eine separate Deutschkenntnisse-Frage gibt
        german_question = None
        qualification_question = None
        
        for q in questions:
            if 'deutschkenntnisse' in q.get('question', '').lower():
                german_question = q
            if 'abschluss' in q.get('question', '').lower():
                qualification_question = q
        
        if german_question:
            print("   ✅ Separate Deutschkenntnisse-Frage gefunden:")
            print(f"      ID: {german_question.get('id')}")
            print(f"      Frage: {german_question.get('question')}")
            print(f"      Type: {german_question.get('question_type')}")
            if german_question.get('preamble'):
                print(f"      Preamble: {german_question.get('preamble')}")
        else:
            print("   ⚠️  KEINE separate Deutschkenntnisse-Frage gefunden!")
        
        print()
        
        if qualification_question:
            print("   📋 Abschluss-Frage:")
            print(f"      Frage: {qualification_question.get('question')}")
            print(f"      Optionen: {qualification_question.get('options')}")
            
            # Prüfe ob Deutschkenntnisse in den Optionen sind
            options = qualification_question.get('options', [])
            has_german_in_options = any('deutsch' in opt.lower() for opt in options)
            
            if has_german_in_options:
                print("      ❌ FEHLER: Deutschkenntnisse sind noch in den Optionen!")
            else:
                print("      ✅ Deutschkenntnisse NICHT in den Optionen (korrekt!)")
        
        # Speichere Output
        output_file = "Output_ordner/Test_German_Skills.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Output gespeichert: {output_file}")
        
    else:
        print(f"❌ FEHLER: {response.status_code}")
        print(f"   {response.text[:500]}")

except Exception as e:
    elapsed = time.time() - start_time
    print(f"❌ FEHLER nach {elapsed:.2f} Sekunden: {e}")

print("=" * 70)

