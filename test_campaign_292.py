"""
Test fuer Kampagne 292 - Pflegefachkraft Hamburg
"""
import requests
import json

# Gespraechsprotokoll fuer Kampagne 292
test_protocol = {
    "id": 292,
    "name": "Pflegefachkraft Hamburg",
    "pages": [
        {
            "id": 1,
            "name": "Der Bewerber erfuellt folgende Kriterien:",
            "position": 1,
            "prompts": [
                {"id": 1, "question": "zwingend: Exam. Pflegefachkraft oder OTA", "position": 1},
                {"id": 2, "question": "alternativ: Bei OTA-Ausbildung auch ohne Erfahrung moeglich", "position": 2},
                {"id": 3, "question": "zwingend: Berufserfahrung von min. 1 Jahr im Operationsbereich notwendig", "position": 3},
                {"id": 4, "question": "Bitte keine Altenpflegekraefte, Pflegehelfer oder Kraefte aus dem Rettungsdienst", "position": 4}
            ]
        },
        {
            "id": 2,
            "name": "Der Bewerber akzeptiert folgende Rahmenbedingungen:",
            "position": 2,
            "prompts": [
                {"id": 5, "question": "Vollzeit (38,5 Wochenstunden)", "position": 1},
                {"id": 6, "question": "Teilzeit (flexibel)", "position": 2},
                {"id": 7, "question": "Fruehdienst Beginn 07:00, Spaetdienst Beginn zw. 09:00 und 12:00h", "position": 3},
                {"id": 8, "question": "Spaetestes Dienstende ist 20:30h aber sehr selten", "position": 4}
            ]
        },
        {
            "id": 3,
            "name": "Weitere Informationen",
            "position": 3,
            "prompts": [
                {"id": 9, "question": "Standort: Martinistrasse 78 20251 Hamburg", "position": 1},
                {"id": 10, "question": "Krankenhaus fuehrt ausschliesslich elektive Operationen durch, es gibt keine Notaufnahme; Dienste sind planbarer als bei Haeusern mit Notaufnahme", "position": 2},
                {"id": 11, "question": "kein Wochenend- und Nachtdienst im Funktionsbereich.", "position": 3},
                {"id": 12, "question": "Schwerpunkt Chirurgie und Orthopaedie, aber auch alle anderen Fachrichtungen bis auf Herz und Kopf", "position": 4},
                {"id": 13, "question": "Zuschuss von zum HVV-Premium-Ticket (auch Deutschlandticket) fuer einen Eigenbetrag von 16,55 Euro", "position": 5},
                {"id": 14, "question": "Firmenfitness-Programm von EGYM", "position": 6},
                {"id": 15, "question": "Freizeitausgleich in den Sommermonaten, zwischen Weihnachten und Neujahr ist die Klinik geschlossen", "position": 7}
            ]
        }
    ]
}

headers = {
    "Authorization": "Bearer 8f15988e07ad5bef0a7050e91b7f3ebe",
    "Content-Type": "application/json"
}

print("=" * 70)
print("TEST: Kampagne 292 - Pflegefachkraft Hamburg")
print("=" * 70)
print()
print("Sending protocol to Render.com...")

response = requests.post(
    "https://voice-ki-backend.onrender.com/webhook/process-protocol",
    json=test_protocol,
    headers=headers,
    timeout=120
)

print(f"Status: {response.status_code}")
print()

result = response.json()

if response.status_code != 200:
    print(f"ERROR: {result}")
else:
    print(f"Response Keys: {list(result.keys())}")
    print(f"Question Count: {result.get('question_count', 0)}")
    print()
    
    # Check for error in knowledge_base
    kb = result.get("knowledge_base", {})
    if kb.get("error"):
        print("=" * 70)
        print("ERROR IN KNOWLEDGE BASE:")
        print(f"  Type: {kb.get('error_type')}")
        print(f"  Message: {kb.get('error')}")
        print("=" * 70)
    
    print("=" * 70)
    print("QUESTIONS")
    print("=" * 70)
    for i, q in enumerate(result.get("questions", []), 1):
        print(f"\n{i}. {q['id']}")
        print(f"   Question: {q['question']}")
        print(f"   Type: {q['type']}")
        if q.get("options"):
            print(f"   Options: {q['options']}")
        if q.get("preamble"):
            print(f"   Preamble: {q['preamble']}")
        gate_config = q.get('gate_config')
        if gate_config:
            print(f"   Gate: {gate_config.get('is_gate', False)}")
        else:
            print(f"   Gate: False")
    
    print()
    print("=" * 70)
    print("KNOWLEDGE BASE")
    print("=" * 70)
    for key, value in kb.items():
        if value and key not in ['error', 'error_type']:
            print(f"\n{key}:")
            print(json.dumps(value, ensure_ascii=False, indent=2))

print()
print("=" * 70)
print("DONE")
print("=" * 70)


