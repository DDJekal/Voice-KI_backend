"""
Test Rahmen-Extractor - Debug Output
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://voice-ki-backend.onrender.com"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# Test-Protokoll
protocol = {
    "id": 5729,
    "name": "Pflegedienstleitung (PDL) - Korian",
    "pages": [
        {
            "id": 1,
            "name": "Seite 1",
            "position": 1,
            "prompts": [
                {
                    "id": 1,
                    "position": 1,
                    "question": "Kriterien",
                    "content": """
Der Bewerber erfüllt folgende Kriterien:

zwingend: Abgeschlossene Berufsausbildung in der Alten- bzw. Gesundheits- und Krankenpflege
zwingend: Anerkannte Weiterbildung zur Pflegedienstleitung
Deutsch B2

Der Bewerber akzeptiert folgende Rahmenbedingungen:

Vollzeit
Teilzeit

Grundgehalt: Das monatliche Grundgehalt kann bis zu 5.180 € betragen

Attraktives KORIAN-Vergütungsmodell mit transparenter Gehaltsentwicklung nach Worx
30 Tage Urlaub in der 5-Tage-Woche, großzügige Sonderurlaubstage und Jubiläumsprämien

Weitere Informationen

AP: Anissa Ben Attia
wichtig für die QS: LL an Anissa Ben Attia HRSBR30@korian.de wtl.
( Hinweis Standort)

Standortmöglichkeit a) Haus am Giesinger Bahnhof München-Giesing// • JobID 5729 – PDL Giesing
Standortmöglichkeit b) Betreuung und Pflege zuhause Germering // • JobID 5760 – PDL Germering
Standortmöglichkeit c) Friedrich-Engels-Bogen 4, 81735 München ( Neuperlach) • JobID 4655 – PDL Neuperlach

Benefits: siehe Korianliste
"""
                }
            ]
        }
    ]
}

print("=" * 80)
print("TEST: Rahmen-Extraktor Debug")
print("=" * 80)

# Request mit Logging
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {WEBHOOK_SECRET}"
}

response = requests.post(
    f"{API_URL}/webhook/process-protocol",
    headers=headers,
    json=protocol,
    timeout=120
)

print(f"\nStatus: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    questions = data.get("questions", [])
    
    print(f"\nGESAMT: {len(questions)} Fragen")
    
    # Suche Gehaltsfrage
    salary_q = [q for q in questions if "gehalt" in q.get("id", "").lower() or "salary" in q.get("id", "").lower()]
    
    if salary_q:
        print("\n[OK] GEHALTSFRAGE GEFUNDEN:")
        for q in salary_q:
            print(f"  ID: {q['id']}")
            print(f"  Frage: {q['question']}")
            print(f"  Preamble: {q.get('preamble', 'None')}")
    else:
        print("\n[FEHLT] KEINE GEHALTSFRAGE!")
    
    # Suche Benefits
    benefits_found = False
    for q in questions:
        preamble = q.get("preamble", "") or ""
        question = q.get("question", "") or ""
        
        if "urlaub" in preamble.lower() or "benefit" in preamble.lower():
            benefits_found = True
            print(f"\n[OK] BENEFITS IN PREAMBLE:")
            print(f"  ID: {q['id']}")
            print(f"  Preamble: {preamble[:100]}...")
            break
    
    if not benefits_found:
        print("\n[FEHLT] KEINE BENEFITS IN PREAMBLES!")
    
    # Zeige alle Fragen
    print("\n" + "=" * 80)
    print("ALLE FRAGEN:")
    print("=" * 80)
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. {q['question']}")
        print(f"   ID: {q['id']}")
        print(f"   Typ: {q['type']}")
        if q.get('preamble'):
            print(f"   Preamble: {q['preamble'][:80]}...")

else:
    print(f"\nFehler: {response.text}")

