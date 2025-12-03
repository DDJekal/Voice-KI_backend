"""
Test Policy-System mit Mock-Daten

Testet das Policy-System ohne API-Zugriff mit lokalen Mock-Daten.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.questions.builder import build_question_catalog


async def test_with_mock_data():
    """Test Policy-System mit Mock Protocol"""
    
    print("\n" + "="*70)
    print("🧪 TEST: Policy-System mit Mock-Daten")
    print("="*70)
    print("Policy Level: standard")
    print("="*70 + "\n")
    
    try:
        # Lade Mock Protocol
        print("📥 Lade Mock Protocol...")
        with open('mock_protocol.json', 'r', encoding='utf-8') as f:
            protocol = json.load(f)
        
        print(f"   ✅ Protocol: {protocol.get('name', 'Mock Campaign')}")
        print(f"   ✅ Pages: {len(protocol.get('pages', []))}")
        print(f"   ✅ Prompts: {sum(len(p.get('prompts', [])) for p in protocol.get('pages', []))}")
        
        # Generiere Questions mit Policies
        print("\n🤖 Generiere Questions mit OpenAI + Policies...")
        print("   (Dies kann 10-30 Sekunden dauern...)\n")
        
        context = {"policy_level": "standard"}
        catalog = await build_question_catalog(protocol, context)
        
        # Ergebnisse anzeigen
        print("\n" + "="*70)
        print("✅ QUESTION CATALOG ERFOLGREICH GENERIERT!")
        print("="*70)
        
        print(f"\n📊 Statistiken:")
        print(f"   Total Questions: {len(catalog.questions)}")
        print(f"   Required: {sum(1 for q in catalog.questions if q.required)}")
        print(f"   Optional: {sum(1 for q in catalog.questions if not q.required)}")
        
        # Policy stats
        if catalog.meta.policies_applied:
            print(f"\n🔧 Policy-Enhancements:")
            print(f"   Policies angewendet: {len(catalog.meta.policies_applied)}")
            
            with_slots = sum(1 for q in catalog.questions if q.slot_config)
            with_hints = sum(1 for q in catalog.questions if q.conversation_hints)
            with_triggers = sum(1 for q in catalog.questions 
                               if q.gate_config and q.gate_config.context_triggers)
            
            print(f"   Fragen mit Slot-Config: {with_slots}")
            print(f"   Fragen mit Conversation-Hints: {with_hints}")
            print(f"   Fragen mit Keyword-Triggers: {with_triggers}")
            
            print(f"\n   📋 Angewendete Policies (erste 10):")
            for policy in catalog.meta.policies_applied[:10]:
                print(f"     • {policy}")
        else:
            print(f"\n   ℹ️  Policies deaktiviert")
        
        # Group by category
        categories = {}
        for q in catalog.questions:
            cat = q.category or "uncategorized"
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n   📁 Kategorien:")
        for cat, count in sorted(categories.items()):
            print(f"     • {cat}: {count} Frage(n)")
        
        # Speichern
        print(f"\n💾 Speichere Output...")
        output_file = 'mock_questions_output.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(catalog.model_dump(by_alias=True), f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ Gespeichert: {output_file}")
        
        # Beispiel-Frage zeigen
        if catalog.questions:
            print(f"\n📝 Beispiel-Frage mit Policies:")
            q = catalog.questions[0]
            print(f"   ID: {q.id}")
            print(f"   Frage: {q.question}")
            if q.slot_config:
                print(f"   Slot: {q.slot_config.fills_slot}")
            if q.conversation_hints:
                print(f"   Hints: ✓ vorhanden")
            if q.gate_config:
                print(f"   Gate: ✓ vorhanden")
        
        print("\n" + "="*70)
        print("✅ TEST ERFOLGREICH!")
        print("="*70)
        print(f"\n💡 Prüfe die Datei '{output_file}' für Details")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_with_mock_data())

