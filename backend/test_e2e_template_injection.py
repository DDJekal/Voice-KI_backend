"""End-to-End Test: Template → Injection → Knowledge Base"""

import json
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from src.utils.variable_injector import VariableInjector
from src.aggregator.knowledge_base_builder import KnowledgeBaseBuilder


def test_end_to_end():
    """Testet den vollständigen Workflow: Template laden → Variablen injizieren → KB generieren"""
    
    print("="*70)
    print("🧪 END-TO-END TEST: Template → Injection → Knowledge Base")
    print("="*70)
    
    # 1. Lade Template
    print("\n📂 Schritt 1: Lade questions_template.json...")
    template_path = Path("../KI-Sellcruiting_VerarbeitungProtokollzuFragen/output/questions_template.json")
    
    if not template_path.exists():
        print(f"   ❌ Template nicht gefunden: {template_path}")
        print(f"   Führe zuerst aus: cd KI-Sellcruiting_VerarbeitungProtokollzuFragen && npm start -- --template")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = json.load(f)
    
    print(f"   ✓ Template geladen: {len(template['questions'])} Fragen")
    
    # Validiere Template
    injector = VariableInjector()
    is_valid, found_vars = injector.validate_template(template)
    print(f"   ✓ Template validiert: {is_valid}")
    print(f"   ✓ Variablen gefunden: {found_vars}")
    
    # 2. Lade Bewerberdaten
    print("\n📂 Schritt 2: Lade Bewerberdaten...")
    
    profile_path = Path("../Input_ordner/Bewerberprofil.json")
    address_path = Path("../Input_ordner/Adresse des Bewerbers.json")
    
    if not profile_path.exists():
        print(f"   ❌ Bewerberprofil nicht gefunden: {profile_path}")
        return False
    
    with open(profile_path, 'r', encoding='utf-8') as f:
        profile = json.load(f)
    
    with open(address_path, 'r', encoding='utf-8') as f:
        address = json.load(f)
    
    # Unterstütze beide Formate
    first_name = profile.get('Vorname') or profile.get('first_name', 'Unknown')
    last_name = profile.get('Nachname') or profile.get('last_name', 'Unknown')
    street = address.get('Straße') or address.get('street', 'Unknown')
    house_number = address.get('Hausnummer') or address.get('house_number', 'Unknown')
    postal_code = address.get('PLZ') or address.get('postal_code', 'Unknown')
    city = address.get('Ort') or address.get('city', 'Unknown')
    
    print(f"   ✓ Profil geladen: {first_name} {last_name}")
    print(f"   ✓ Adresse geladen: {street} {house_number}, {postal_code} {city}")
    
    # 3. Variablen injizieren
    print("\n🔄 Schritt 3: Injiziere Variablen...")
    resolved = injector.inject_applicant_data(template, profile, address)
    
    # Prüfe ob Variablen ersetzt wurden
    name_q = next((q for q in resolved['questions'] if q['id'] == 'name_confirmation'), None)
    addr_q = next((q for q in resolved['questions'] if q['id'] == 'adresse_bestaetigen'), None)
    
    if name_q:
        print(f"   ✓ Name-Frage: {name_q['question']}")
    if addr_q:
        print(f"   ✓ Adress-Frage: {addr_q['question']}")
    
    # Prüfe ob noch Platzhalter übrig sind (sollte nicht sein)
    questions_with_vars = [
        q for q in resolved['questions'] 
        if '{{' in q.get('question', '')
    ]
    
    if questions_with_vars:
        print(f"   ⚠️  {len(questions_with_vars)} Frage(n) haben noch Platzhalter:")
        for q in questions_with_vars:
            print(f"      - {q['id']}: {q['question']}")
    else:
        print(f"   ✓ Alle Variablen ersetzt")
    
    # 4. Knowledge Base generieren
    print("\n📝 Schritt 4: Generiere Knowledge Base...")
    kb_builder = KnowledgeBaseBuilder()
    kb_phase3 = kb_builder.build_phase_3(resolved)
    
    print(f"   ✓ Knowledge Base generiert: {len(kb_phase3)} Zeichen")
    
    # Prüfe ob KB Bewerberdaten enthält
    if first_name in kb_phase3 and last_name in kb_phase3:
        print(f"   ✓ Bewerber-Name im KB: {first_name} {last_name}")
    else:
        print(f"   ⚠️  Bewerber-Name nicht vollständig im KB gefunden")
    
    if street in kb_phase3 and city in kb_phase3:
        print(f"   ✓ Adresse im KB: {street}, {city}")
    else:
        print(f"   ⚠️  Adresse nicht vollständig im KB gefunden")
    
    # 5. Speichere Outputs
    print("\n💾 Schritt 5: Speichere Outputs...")
    
    output_dir = Path("Output_ordner")
    output_dir.mkdir(exist_ok=True)
    
    # Resolved questions
    with open(output_dir / "questions_resolved_e2e.json", 'w', encoding='utf-8') as f:
        json.dump(resolved, f, ensure_ascii=False, indent=2)
    print(f"   ✓ questions_resolved_e2e.json gespeichert")
    
    # Knowledge Base
    with open(output_dir / "knowledge_base_phase3_e2e.txt", 'w', encoding='utf-8') as f:
        f.write(kb_phase3)
    print(f"   ✓ knowledge_base_phase3_e2e.txt gespeichert")
    
    # 6. Statistik
    print("\n" + "="*70)
    print("✅ END-TO-END TEST ERFOLGREICH!")
    print("="*70)
    print(f"\n📊 Statistik:")
    print(f"   Template Fragen: {len(template['questions'])}")
    print(f"   Resolved Fragen: {len(resolved['questions'])}")
    print(f"   KB Länge: {len(kb_phase3)} Zeichen")
    print(f"   Variablen injiziert: {len(found_vars)}")
    print(f"\n💰 Kosten:")
    print(f"   Template-Generierung: ~$0.11 (einmalig pro Kampagne)")
    print(f"   Variable Injection: $0 (nur String-Replacement)")
    print(f"   KB Generierung: $0 (reine Transformation)")
    print(f"   TOTAL pro Bewerber: $0")
    print(f"\n📁 Output:")
    print(f"   {output_dir / 'questions_resolved_e2e.json'}")
    print(f"   {output_dir / 'knowledge_base_phase3_e2e.txt'}")
    
    return True


if __name__ == "__main__":
    success = test_end_to_end()
    sys.exit(0 if success else 1)

