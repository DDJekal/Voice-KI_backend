"""Test Variable Injector - Testet die Variable Substitution"""

import json
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from src.utils.variable_injector import VariableInjector


def test_variable_injection():
    """Testet die Variable Injection mit Beispieldaten"""
    
    print("="*70)
    print("🧪 TEST: Variable Injector")
    print("="*70)
    
    # 1. Erstelle Template mit Platzhaltern
    template = {
        "_meta": {
            "schema_version": "1.0",
            "generated_at": "2025-10-28T10:00:00Z",
            "generator": "test"
        },
        "questions": [
            {
                "id": "name_confirmation",
                "question": "Spreche ich mit {{candidatefirst_name}} {{candidatelast_name}}?",
                "type": "boolean",
                "required": True,
                "priority": 1,
                "category": "identifikation",
                "data_source": "applicant_profile"
            },
            {
                "id": "adresse_bestaetigen",
                "question": "Ich habe Ihre Adresse als {{street}} {{house_number}}, {{postal_code}} {{city}}. Ist das korrekt?",
                "type": "boolean",
                "required": True,
                "priority": 1,
                "category": "identifikation",
                "data_source": "applicant_address"
            },
            {
                "id": "telephone_confirm",
                "question": "Ihre Telefonnummer ist {{telephone}}, korrekt?",
                "type": "boolean",
                "required": False,
                "priority": 2,
                "category": "kontaktinformationen",
                "help_text": "Unter {{telephone}} können wir Sie erreichen"
            }
        ]
    }
    
    # 2. Erstelle Bewerberdaten
    profile = {
        "Vorname": "Max",
        "Nachname": "Mustermann",
        "Email": "max.mustermann@example.de",
        "Telefonnummer": "017600000"
    }
    
    address = {
        "Straße": "Musterstraße",
        "Hausnummer": "42",
        "PLZ": "70376",
        "Ort": "Stuttgart"
    }
    
    print("\n📝 Template (vor Injection):")
    print(f"   Frage 1: {template['questions'][0]['question']}")
    print(f"   Frage 2: {template['questions'][1]['question']}")
    print(f"   Frage 3: {template['questions'][2]['question']}")
    
    # 3. Variable Injection durchführen
    injector = VariableInjector()
    
    print("\n🔄 Validiere Template...")
    is_valid, found_vars = injector.validate_template(template)
    print(f"   ✓ Template valid: {is_valid}")
    print(f"   ✓ Gefundene Variablen: {found_vars}")
    
    print("\n🔄 Injiziere Bewerberdaten...")
    resolved = injector.inject_applicant_data(template, profile, address)
    
    # 4. Ergebnisse prüfen
    print("\n✅ Resolved (nach Injection):")
    print(f"   Frage 1: {resolved['questions'][0]['question']}")
    print(f"   Frage 2: {resolved['questions'][1]['question']}")
    print(f"   Frage 3: {resolved['questions'][2]['question']}")
    print(f"   Help Text: {resolved['questions'][2]['help_text']}")
    
    # 5. Assertions
    print("\n🧪 Assertions:")
    
    expected_q1 = "Spreche ich mit Max Mustermann?"
    actual_q1 = resolved['questions'][0]['question']
    assert actual_q1 == expected_q1, f"Expected '{expected_q1}', got '{actual_q1}'"
    print(f"   ✓ Name-Bestätigung korrekt")
    
    expected_q2 = "Ich habe Ihre Adresse als Musterstraße 42, 70376 Stuttgart. Ist das korrekt?"
    actual_q2 = resolved['questions'][1]['question']
    assert actual_q2 == expected_q2, f"Expected '{expected_q2}', got '{actual_q2}'"
    print(f"   ✓ Adress-Bestätigung korrekt")
    
    expected_q3 = "Ihre Telefonnummer ist 017600000, korrekt?"
    actual_q3 = resolved['questions'][2]['question']
    assert actual_q3 == expected_q3, f"Expected '{expected_q3}', got '{actual_q3}'"
    print(f"   ✓ Telefon-Bestätigung korrekt")
    
    expected_help = "Unter 017600000 können wir Sie erreichen"
    actual_help = resolved['questions'][2]['help_text']
    assert actual_help == expected_help, f"Expected '{expected_help}', got '{actual_help}'"
    print(f"   ✓ Help Text korrekt")
    
    # 6. Teste ohne Adresse
    print("\n🧪 Test ohne Adresse (nur Profil):")
    resolved_no_addr = injector.inject_applicant_data(template, profile, None)
    print(f"   Frage 2 (mit missing vars): {resolved_no_addr['questions'][1]['question']}")
    
    # Adress-Variablen sollten nicht ersetzt werden
    assert "{{street}}" in resolved_no_addr['questions'][1]['question']
    print(f"   ✓ Variablen ohne Daten bleiben erhalten")
    
    print("\n" + "="*70)
    print("✅ ALLE TESTS ERFOLGREICH!")
    print("="*70)


if __name__ == "__main__":
    test_variable_injection()

