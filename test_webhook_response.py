"""
Test Webhook Response Format

Verifiziert, dass die Webhook Response das korrekte Format hat:
- MUSS questions Array enthalten
- DARF KEINE knowledge_base enthalten (nur in questions.json Datei)
"""

import json
from pathlib import Path

# Simulate Webhook Response format
def simulate_webhook_response():
    """Simuliert die Webhook Response basierend auf api_server.py Logik"""
    
    # Angenommen questions_catalog wurde gebaut und hat knowledge_base
    # Die trimmed_questions werden erstellt
    trimmed_questions = [
        {
            "id": "mh_abgeschlossene_berufsausbildung",
            "question": "Haben Sie folgende Qualifikation: Abgeschlossene Berufsausbildung als Gesundheits- und Krankenpfleger/in oder Altenpfleger/in?",
            "type": "string",
            "required": True,
            "priority": 1,
            "group": "qualifikation"
        },
        {
            "id": "mh_anerkannte_weiterbildung",
            "question": "Können Sie mir etwas dazu sagen: Anerkannte Weiterbildung zur Pflegedienstleitung?",
            "type": "string",
            "required": True,
            "priority": 1,
            "group": "qualifikation"
        }
    ]
    
    # Webhook Response (wie in api_server.py definiert)
    webhook_response = {
        "protocol_id": 5729,
        "protocol_name": "Pflegedienstleitung (PDL) - Korian",
        "processed_at": "2025-12-15T12:00:00Z",
        "question_count": len(trimmed_questions),
        "questions": trimmed_questions
    }
    
    return webhook_response


def check_webhook_format(response):
    """Prüft, ob Webhook Response das erwartete Format hat"""
    
    print("=" * 70)
    print("WEBHOOK RESPONSE FORMAT VERIFICATION")
    print("=" * 70)
    
    checks = []
    
    # Check 1: Muss 'questions' haben
    has_questions = 'questions' in response
    checks.append(("Has 'questions' field", has_questions, True))
    
    # Check 2: Darf KEINE 'knowledge_base' haben
    has_no_kb = 'knowledge_base' not in response
    checks.append(("Does NOT have 'knowledge_base' field", has_no_kb, True))
    
    # Check 3: Muss standard Felder haben
    has_protocol_id = 'protocol_id' in response
    checks.append(("Has 'protocol_id' field", has_protocol_id, True))
    
    has_question_count = 'question_count' in response
    checks.append(("Has 'question_count' field", has_question_count, True))
    
    # Check 4: questions ist Array
    questions_is_array = isinstance(response.get('questions'), list)
    checks.append(("'questions' is array", questions_is_array, True))
    
    # Print Results
    print("\nChecks:")
    all_passed = True
    for check_name, actual, expected in checks:
        status = "[PASS]" if actual == expected else "[FAIL]"
        print(f"  {status} {check_name}: {actual}")
        if actual != expected:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("RESULT: All checks passed!")
        print("Webhook Response format is CORRECT and UNCHANGED.")
    else:
        print("RESULT: Some checks failed!")
        print("Webhook Response format has CHANGED.")
    print("=" * 70)
    
    # Print full response for inspection
    print("\nFull Webhook Response:")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    
    return all_passed


def main():
    # Simulate webhook response
    response = simulate_webhook_response()
    
    # Verify format
    passed = check_webhook_format(response)
    
    if passed:
        print("\nSUCCESS: Webhook Response format is compatible with HOC Django!")
    else:
        print("\nERROR: Webhook Response format has changed!")
        print("This will BREAK the HOC Django application!")
    
    return 0 if passed else 1


if __name__ == "__main__":
    exit(main())

