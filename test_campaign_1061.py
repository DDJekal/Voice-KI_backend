"""
Test fuer Kampagne 1061 - Paedagogische Fachkraft Muenchen
"""
import requests
import json

# Gespraechsprotokoll fuer Kampagne 1061
test_protocol = {
    "id": 1061,
    "name": "Paedagogische Fachkraft - Muenchen",
    "pages": [
        {
            "id": 1,
            "name": "Der Bewerber erfuellt folgende Kriterien:",
            "position": 1,
            "prompts": [
                {"id": 1, "question": "Zwingend: Einschlaegige paedagogische Berufsausbildung", "position": 1},
                {"id": 2, "question": "Deutsch B2", "position": 2}
            ]
        },
        {
            "id": 2,
            "name": "Der Bewerber erfuellt folgende Rahmenbedingungen:",
            "position": 2,
            "prompts": [
                {"id": 3, "question": "Teilzeit: flexibel", "position": 1},
                {"id": 4, "question": "Vollzeit", "position": 2}
            ]
        },
        {
            "id": 3,
            "name": "Weitere Informationen",
            "position": 3,
            "prompts": [
                {"id": 5, "question": "Standort: Diverse Standorte innerhalb des Stadtgebiets von Muenchen. Muss im Zweitgespraech geklaert werden", "position": 1},
                {"id": 6, "question": "Taetigkeit: Selbstaendige Erledigung administrativer Aufgaben fuer Jugendliche und Einrichtung", "position": 2},
                {"id": 7, "question": "Taetigkeit: Betreuung von Jugendlichen in Gruppen- und Einzelarbeit im Wohngruppen-Alltag", "position": 3},
                {"id": 8, "question": "Taetigkeit: Vertrauensbetreuerschaft und Fallverantwortung fuer zwei Jugendliche", "position": 4},
                {"id": 9, "question": "Taetigkeit: Schul- und Ausbildungsbegleitung der Bezugsjugendlichen", "position": 5},
                {"id": 10, "question": "Taetigkeit: Planung und Durchfuehrung von Freizeiten, Milieutherapie, Unternehmungen, Gruppenabenden", "position": 6},
                {"id": 11, "question": "Taetigkeit: Zusammenarbeit mit Jugendaemtern, Schulen, Therapeut*innen, Kliniken und diversen Fachstellen", "position": 7}
            ]
        }
    ]
}

headers = {
    "Authorization": "Bearer 8f15988e07ad5bef0a7050e91b7f3ebe",
    "Content-Type": "application/json"
}

print("=" * 70)
print("TEST: Kampagne 1061 - Paedagogische Fachkraft Muenchen")
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
    
    print("=" * 70)
    print("QUESTIONS")
    print("=" * 70)
    for i, q in enumerate(result.get("questions", []), 1):
        print(f"\n{i}. {q['id']}")
        print(f"   Question: {q['question']}")
        print(f"   Type: {q['type']}")
        if q.get("preamble"):
            print(f"   Preamble: {q['preamble']}")
        print(f"   Gate: {q.get('gate_config', {}).get('is_gate', False)}")
    
    print()
    print("=" * 70)
    print("KNOWLEDGE BASE")
    print("=" * 70)
    kb = result.get("knowledge_base", {})
    for key, value in kb.items():
        if value:
            print(f"\n{key}:")
            print(json.dumps(value, ensure_ascii=False, indent=2))

print()
print("=" * 70)
print("DONE")
print("=" * 70)


