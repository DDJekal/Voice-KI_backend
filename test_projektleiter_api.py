import requests
import json
import time

# Konfiguration
API_URL = "https://voice-ki-backend.onrender.com/webhook/process-protocol"
WEBHOOK_SECRET = "8f15988e07ad5bef0a7050e91b7f3ebe"

# Projektleiter Protokoll
protocol = {
    "id": 63,
    "name": "Projektleiter",
    "pages": [
        {
            "id": 90,
            "name": "Der Bewerber erfüllt folgende Kriterien:",
            "position": 1,
            "prompts": [
                {"id": 321, "question": "wünschenswert: Führerschein", "position": 1},
                {"id": 319, "question": "alternativ: Ausbildung zur Elektrofachkraft (m/w/d)", "position": 2},
                {"id": 317, "question": "alternativ: Ausbildung zum Elektriker/ Elektrotechniker/ Elektroniker (m/w/d)", "position": 3},
                {"id": 315, "question": "zwingend: min 2. Jahre Berufserfahrung in Deutschland", "position": 4},
                {"id": 313, "question": "zwingend: Studium Elektrotechnik oder in einem eng verwandten Bereich", "position": 5},
                {"id": 311, "question": "Deutsch B2", "position": 6}
            ]
        },
        {
            "id": 91,
            "name": "Der Bewerber akzeptiert folgende Rahmenbedingungen:",
            "position": 2,
            "prompts": [
                {"id": 327, "question": "Unbefristeter Arbeitsvertrag bei einem zuverlässigen Arbeitgeber", "position": 1},
                {"id": 325, "question": "Attraktives Grundgehalt plus leistungsabhängige Erfolgsbeteiligung möglich( Gaber zahlt min. 10 % mehr als der jetzige Arbeitgeber!", "position": 2},
                {"id": 323, "question": "Vollzeit", "position": 3}
            ]
        },
        {
            "id": 92,
            "name": "Weitere Informationen",
            "position": 3,
            "prompts": [
                {"id": 345, "question": "kein Fremdfinanziertes Unternhemen - stehen sicher am Markt und finanzieren sich aus eigener Kraft (nicht wie viele andere Unternehmen im Energiebereich die sich groß präsentieren, aber dann schnell wieder abstürzen", "position": 1},
                {"id": 343, "question": "breit aufgestellt Einsatzfelder: Photov., Windkraft, Unternehmen, Netzbetreiber, E-Mobilität (Ladesationen)", "position": 2},
                {"id": 341, "question": "Full-Service-Unternehmen: übernehemen jeden Schritt beim Kunden von Anschluss und Transport bis zu den regelmäßigen Wartungen am Ende", "position": 3},
                {"id": 339, "question": "große Solarparks und nicht nur eine kleine Photov. Anlage aufs Dach (Also punkt 1 große Projekte)", "position": 4},
                {"id": 337, "question": "seit 1995: Traditionsunternehmen", "position": 5},
                {"id": 335, "question": "deutsche Qualität: Produktion in DE (schnelle Lieferzeiten+Kompatibil in allen deutschen Mittelspannungnetzen)", "position": 6},
                {"id": 333, "question": "stehen für nachhaltige Zukunft und erneubare Energien", "position": 7},
                {"id": 331, "question": "Standort: Am Fichtenkamp 7-9 Bünde", "position": 8},
                {"id": 329, "question": "AP : Hergert hergert@faber-etec.de", "position": 9}
            ]
        }
    ]
}

# Request vorbereiten
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {WEBHOOK_SECRET}"
}

# Body ist direkt das Protokoll (nicht unter "protocol_data")
body = protocol

# Request senden mit Zeitmessung
print("=" * 70)
print("🚀 VoiceKI API Test - Projektleiter Protokoll")
print("=" * 70)
print(f"📡 URL: {API_URL}")
print(f"📄 Kampagne: {protocol['name']}")
print(f"📋 Seiten: {len(protocol['pages'])}")
print(f"⏱️  Start: {time.strftime('%H:%M:%S')}")
print("-" * 70)

start_time = time.time()

try:
    response = requests.post(
        API_URL,
        headers=headers,
        json=body,
        timeout=180  # 3 Minuten Timeout
    )
    
    elapsed = time.time() - start_time
    
    print(f"⏱️  Ende: {time.strftime('%H:%M:%S')}")
    print(f"⚡ Dauer: {elapsed:.2f} Sekunden")
    print(f"📊 Status: {response.status_code}")
    print("-" * 70)
    
    if response.status_code == 200:
        result = response.json()
        questions = result.get('questions', [])
        meta = result.get('meta', {})
        
        print("✅ ERFOLG!")
        print(f"   📝 Fragen generiert: {len(questions)}")
        print(f"   ⭐ Required: {meta.get('required_count', 0)}")
        print(f"   💡 Optional: {meta.get('optional_count', 0)}")
        
        # Fragen nach Phase gruppieren
        phases = {}
        for q in questions:
            phase = q.get('phase', 'unknown')
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(q)
        
        print(f"\n   📊 Verteilung nach Phasen:")
        for phase in sorted(phases.keys()):
            print(f"      Phase {phase}: {len(phases[phase])} Fragen")
        
        # Optional: Output speichern
        output_file = "Output_ordner/Projektleiter_Output.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Output gespeichert: {output_file}")
        
        # Erste 3 Fragen anzeigen
        print(f"\n📋 Erste 3 Fragen:")
        for i, q in enumerate(questions[:3], 1):
            question_text = q.get('question') or q.get('text') or '(keine Frage)'
            print(f"\n   {i}. [{q.get('type')}] {question_text}")
            if q.get('options'):
                print(f"      Optionen: {len(q.get('options'))} Auswahlmöglichkeiten")
            if q.get('preamble'):
                print(f"      Preamble: {q.get('preamble')[:60]}...")
        
    else:
        print(f"❌ FEHLER: {response.status_code}")
        print(f"   {response.text}")

except requests.exceptions.Timeout:
    elapsed = time.time() - start_time
    print(f"⏰ TIMEOUT nach {elapsed:.2f} Sekunden!")
    print("   Der Server antwortet nicht. Möglicherweise Cold Start oder Server-Problem.")
    
except requests.exceptions.ConnectionError as e:
    print(f"❌ VERBINDUNGSFEHLER: {e}")
    print("   Kann den Server nicht erreichen. Ist die URL korrekt?")
    
except Exception as e:
    elapsed = time.time() - start_time
    print(f"❌ FEHLER nach {elapsed:.2f} Sekunden: {e}")

print("=" * 70)

