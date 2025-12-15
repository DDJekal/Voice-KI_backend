"""
Test Must-Have Kategorisierung - Führerschein, Impfung, etc.
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_URL = "https://voice-ki-backend.onrender.com/webhook/process-protocol"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# Test Protocol mit verschiedenen Must-Have Typen
test_protocol = {
    "id": 999,
    "name": "Test: Must-Have Kategorisierung",
    "pages": [
        {
            "id": 1,
            "name": "Anforderungsprofil",
            "position": 1,
            "prompts": [
                {
                    "id": 1,
                    "position": 1,
                    "question": "Zwingend: Führerschein Klasse B",
                    "answer": "Ja, habe ich"
                },
                {
                    "id": 2,
                    "position": 2,
                    "question": "Zwingend: Impfnachweis Masern",
                    "answer": "Ja, vorhanden"
                },
                {
                    "id": 3,
                    "position": 3,
                    "question": "Bereitschaft zu Schichtdienst",
                    "answer": "Ja, flexibel"
                },
                {
                    "id": 4,
                    "position": 4,
                    "question": "Mindestens 2 Jahre Berufserfahrung",
                    "answer": "Ja, über 3 Jahre"
                }
            ]
        },
        {
            "id": 2,
            "name": "Rahmenbedingungen",
            "position": 2,
            "prompts": [
                {
                    "id": 5,
                    "position": 1,
                    "question": "Die Stelle ist in Vollzeit (40 Std/Woche). Passt das?",
                    "answer": "Ja, passt"
                },
                {
                    "id": 6,
                    "position": 2,
                    "question": "Standort Stuttgart",
                    "answer": "Ja, kein Problem"
                }
            ]
        }
    ]
}

def test_musthave_categories():
    """Test ob Must-Haves richtig kategorisiert werden"""
    
    print("Test: Must-Have Kategorisierung")
    print("=" * 60)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WEBHOOK_SECRET}"
    }
    
    try:
        print("Sende Request an API...")
        response = requests.post(
            API_URL,
            headers=headers,
            json=test_protocol,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            questions = result.get("questions", [])
            
            print(f"\n{len(questions)} Fragen generiert\n")
            
            # Analysiere Kategorisierung
            categories_found = {
                "fuehrerschein": [],
                "gesundheit": [],
                "soft_skills": [],
                "sonstige_anforderung": [],
                "andere": []
            }
            
            for q in questions:
                context = q.get("context") or ""
                question_text = q.get("question", "")
                
                # Prüfe Context auf Kategorie
                if "fuehrerschein" in context.lower():
                    categories_found["fuehrerschein"].append(question_text)
                elif "gesundheit" in context.lower():
                    categories_found["gesundheit"].append(question_text)
                elif "soft_skills" in context.lower():
                    categories_found["soft_skills"].append(question_text)
                elif "sonstige_anforderung" in context.lower():
                    categories_found["sonstige_anforderung"].append(question_text)
                else:
                    # Prüfe auch in der Frage selbst
                    if "führerschein" in question_text.lower():
                        categories_found["andere"].append(("Führerschein", question_text))
                    elif "impf" in question_text.lower() or "masern" in question_text.lower():
                        categories_found["andere"].append(("Impfung", question_text))
                    elif "schicht" in question_text.lower():
                        categories_found["andere"].append(("Schichtdienst", question_text))
            
            # Zeige Ergebnisse
            print("KATEGORISIERUNGS-ERGEBNISSE:")
            print("-" * 60)
            
            if categories_found["fuehrerschein"]:
                print("\nFUEHRERSCHEIN (korrekt kategorisiert):")
                for q in categories_found["fuehrerschein"]:
                    print(f"  > {q}")
            
            if categories_found["gesundheit"]:
                print("\nGESUNDHEIT (korrekt kategorisiert):")
                for q in categories_found["gesundheit"]:
                    print(f"  > {q}")
            
            if categories_found["soft_skills"]:
                print("\nSOFT SKILLS (korrekt kategorisiert):")
                for q in categories_found["soft_skills"]:
                    print(f"  > {q}")
            
            if categories_found["sonstige_anforderung"]:
                print("\nSONSTIGE ANFORDERUNGEN (Fallback):")
                for q in categories_found["sonstige_anforderung"]:
                    print(f"  > {q}")
            
            if categories_found["andere"]:
                print("\nNICHT KATEGORISIERT (sollte nicht passieren!):")
                for typ, q in categories_found["andere"]:
                    print(f"  > [{typ}] {q}")
            
            # Zeige alle Fragen mit Context
            print("\n" + "=" * 60)
            print("ALLE FRAGEN MIT CONTEXT:")
            print("=" * 60)
            for i, q in enumerate(questions, 1):
                print(f"\n{i}. {q.get('question', '')}")
                print(f"   Typ: {q.get('question_type', '')}")
                print(f"   Gruppe: {q.get('group', '')}")
                if q.get('context'):
                    print(f"   Context: {q.get('context', '')}")
                if q.get('preamble'):
                    print(f"   Preamble: {q.get('preamble', '')}")
            
            # Speichere Output
            output_file = "Output_ordner/Test_MustHave_Categories.json"
            os.makedirs("Output_ordner", exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            print(f"\nOutput gespeichert: {output_file}")
            
            # Erfolgs-Kriterien
            success = True
            if not categories_found["fuehrerschein"]:
                print("\nFEHLER: Fuehrerschein wurde nicht als 'fuehrerschein' kategorisiert!")
                success = False
            
            if not categories_found["gesundheit"]:
                print("\nFEHLER: Impfnachweis wurde nicht als 'gesundheit' kategorisiert!")
                success = False
            
            if categories_found["andere"]:
                print("\nFEHLER: Einige Must-Haves wurden nicht kategorisiert!")
                success = False
            
            if success:
                print("\n" + "=" * 60)
                print("TEST ERFOLGREICH - Alle Must-Haves korrekt kategorisiert!")
                print("=" * 60)
            
        else:
            print(f"\nAPI Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\nException: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_musthave_categories()

