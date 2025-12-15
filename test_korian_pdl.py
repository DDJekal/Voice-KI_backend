"""
Test: Korian PDL Protokoll - Vollständige Verarbeitung
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://voice-ki-backend.onrender.com/webhook/process-protocol"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# Korian PDL Protokoll
test_protocol = {
    "id": 5729,
    "name": "Pflegedienstleitung (PDL) - Korian",
    "pages": [
        {
            "id": 1,
            "name": "Der Bewerber erfüllt folgende Kriterien",
            "position": 1,
            "prompts": [
                {
                    "id": 1,
                    "position": 1,
                    "question": "zwingend: Abgeschlossene Berufsausbildung in der Alten- bzw. Gesundheits- und Krankenpflege",
                    "answer": "ja"
                },
                {
                    "id": 2,
                    "position": 2,
                    "question": "zwingend: Anerkannte Weiterbildung zur Pflegedienstleitung",
                    "answer": "ja"
                },
                {
                    "id": 3,
                    "position": 3,
                    "question": "Deutsch B2",
                    "answer": "ja"
                }
            ]
        },
        {
            "id": 2,
            "name": "Der Bewerber akzeptiert folgende Rahmenbedingungen",
            "position": 2,
            "prompts": [
                {
                    "id": 4,
                    "position": 1,
                    "question": "Vollzeit",
                    "answer": "ja"
                },
                {
                    "id": 5,
                    "position": 2,
                    "question": "Teilzeit",
                    "answer": "ja"
                },
                {
                    "id": 6,
                    "position": 3,
                    "question": "Grundgehalt: Das monatliche Grundgehalt kann bis zu 5.180 € betragen",
                    "answer": "passt"
                },
                {
                    "id": 7,
                    "position": 4,
                    "question": "Attraktives KORIAN-Vergütungsmodell mit transparenter Gehaltsentwicklung nach Worx",
                    "answer": "interessant"
                },
                {
                    "id": 8,
                    "position": 5,
                    "question": "30 Tage Urlaub in der 5-Tage-Woche, großzügige Sonderurlaubstage und Jubiläumsprämien",
                    "answer": "gut"
                }
            ]
        },
        {
            "id": 3,
            "name": "Standortmöglichkeiten",
            "position": 3,
            "prompts": [
                {
                    "id": 9,
                    "position": 1,
                    "question": "Standortmöglichkeit a) Haus am Giesinger Bahnhof München-Giesing",
                    "answer": "JobID 5729"
                },
                {
                    "id": 10,
                    "position": 2,
                    "question": "Standortmöglichkeit b) Betreuung und Pflege zuhause Germering",
                    "answer": "JobID 5760"
                },
                {
                    "id": 11,
                    "position": 3,
                    "question": "Standortmöglichkeit c) Friedrich-Engels-Bogen 4, 81735 München (Neuperlach)",
                    "answer": "JobID 4655"
                }
            ]
        }
    ]
}

def analyze_questions(questions):
    """Analysiere welche Themen abgedeckt sind"""
    
    categories = {
        "Ausbildung Pflege": False,
        "Weiterbildung PDL": False,
        "Deutschkenntnisse B2": False,
        "Vollzeit/Teilzeit": False,
        "Gehalt (5.180€)": False,
        "Urlaub/Benefits": False,
        "Standorte": False
    }
    
    for q in questions:
        question_lower = q.get("question", "").lower()
        context = (q.get("context") or "").lower()
        preamble = (q.get("preamble") or "").lower()
        
        # Check coverage
        if any(w in question_lower for w in ["ausbildung", "alten", "krankenpflege"]):
            categories["Ausbildung Pflege"] = True
        
        if any(w in question_lower for w in ["weiterbildung", "pflegedienstleitung", "pdl"]):
            categories["Weiterbildung PDL"] = True
        
        if any(w in question_lower for w in ["deutsch", "b2", "sprachkenntnisse"]):
            categories["Deutschkenntnisse B2"] = True
        
        if any(w in question_lower for w in ["vollzeit", "teilzeit", "arbeitszeit"]):
            categories["Vollzeit/Teilzeit"] = True
        
        if "5.180" in question_lower or "5180" in question_lower or "gehalt" in question_lower:
            categories["Gehalt (5.180€)"] = True
        
        if "urlaub" in question_lower or "urlaub" in preamble:
            categories["Urlaub/Benefits"] = True
        
        if any(w in question_lower for w in ["giesing", "germering", "neuperlach", "standort"]):
            categories["Standorte"] = True
    
    return categories

def test_korian_pdl():
    print("=" * 80)
    print("TEST: Korian PDL Protokoll - Vollstaendige Verarbeitung")
    print("=" * 80)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WEBHOOK_SECRET}"
    }
    
    try:
        print("\nSende Request...")
        response = requests.post(
            API_URL,
            headers=headers,
            json=test_protocol,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            result = response.json()
            questions = result.get("questions", [])
            
            print(f"GENERIERTE FRAGEN: {len(questions)}")
            print("=" * 80)
            
            for i, q in enumerate(questions, 1):
                print(f"\n{i}. {q.get('question', '')}")
                print(f"   Typ: {q.get('type', '')}")
                print(f"   Gruppe: {q.get('group', '')}")
                if q.get('options'):
                    print(f"   Optionen: {', '.join(q['options'][:3])}{'...' if len(q['options']) > 3 else ''}")
                if q.get('preamble'):
                    print(f"   Vorwort: {q.get('preamble', '')[:100]}...")
                if q.get('context'):
                    print(f"   Context: {q.get('context', '')}")
            
            # Analyse
            print("\n" + "=" * 80)
            print("ABDECKUNGS-ANALYSE:")
            print("=" * 80)
            
            categories = analyze_questions(questions)
            
            missing = []
            for topic, covered in categories.items():
                status = "OK" if covered else "FEHLT"
                symbol = "[OK]" if covered else "[X]"
                print(f"{symbol} {topic}: {status}")
                if not covered:
                    missing.append(topic)
            
            # Speichern
            output_file = "Output_ordner/Test_Korian_PDL.json"
            os.makedirs("Output_ordner", exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            print(f"\nOutput gespeichert: {output_file}")
            
            # Zusammenfassung
            print("\n" + "=" * 80)
            if missing:
                print(f"FEHLER: {len(missing)} Themen fehlen:")
                for topic in missing:
                    print(f"  - {topic}")
            else:
                print("ERFOLG: Alle Themen abgedeckt!")
            print("=" * 80)
            
        else:
            print(f"API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_korian_pdl()

