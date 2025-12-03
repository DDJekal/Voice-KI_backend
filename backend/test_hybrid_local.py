"""
Test Script für Question Generator mit lokaler JSON-Datei

Testet die automatische Generierung von questions.json aus Gesprächsprotokollen.
"""

import sys
import asyncio
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.questions.builder import build_question_catalog


async def test_with_local_protocol(protocol_file: str, policy_level: str = "standard"):
    """
    Testet Question Generator mit einer lokalen Protocol-Datei.
    
    Args:
        protocol_file: Pfad zur Gesprächsprotokoll-JSON
        policy_level: Policy level zum Testen (basic, standard, advanced)
    """
    print("\n" + "="*70)
    print("TEST: Question Generator (mit lokaler Datei)")
    print("="*70)
    print(f"Protocol File: {protocol_file}")
    print(f"Policy Level: {policy_level}")
    print("="*70 + "\n")
    
    try:
        # Lade Protocol
        protocol_path = Path(protocol_file)
        if not protocol_path.exists():
            print(f"Fehler: Datei nicht gefunden: {protocol_file}")
            return
        
        with open(protocol_path, 'r', encoding='utf-8') as f:
            protocol = json.load(f)
        
        print(f"OK Protocol geladen: {protocol.get('name', 'Unknown')}")
        print(f"OK Pages: {len(protocol.get('pages', []))}")
        
        # Generiere Questions
        print("\nGeneriere questions.json mit OpenAI...")
        print(f"   Policy Level: {policy_level}")
        print("   (Dies kann 10-30 Sekunden dauern...)")
        
        context = {"policy_level": policy_level}
        catalog = await build_question_catalog(protocol, context)
        
        # Ergebnisse anzeigen
        print("\n" + "="*70)
        print("QUESTION CATALOG ERFOLGREICH GENERIERT!")
        print("="*70)
        
        print(f"\nStatistiken:")
        print(f"   Total Questions: {len(catalog.questions)}")
        print(f"   Required: {sum(1 for q in catalog.questions if q.required)}")
        print(f"   Optional: {sum(1 for q in catalog.questions if not q.required)}")
        
        # NEU: Tier-Statistik (Hybrid-Ansatz)
        tier1_count = sum(1 for q in catalog.questions if q.id.startswith('pq_'))
        tier2_count = sum(1 for q in catalog.questions if q.id.startswith('vc_'))
        tier3_count = len(catalog.questions) - tier1_count - tier2_count
        
        print(f"\n3-Tier Hybrid-Ansatz:")
        print(f"   Tier 1 (Protocol Questions): {tier1_count}")
        print(f"   Tier 2 (Verbatim Fallback): {tier2_count}")
        print(f"   Tier 3 (Generated): {tier3_count}")
        
        # NEU: Policy stats
        if catalog.meta.policies_applied:
            print(f"\nPolicy-Enhancements:")
            print(f"   Policies angewendet: {len(catalog.meta.policies_applied)}")
            
            with_slots = sum(1 for q in catalog.questions if q.slot_config)
            with_hints = sum(1 for q in catalog.questions if q.conversation_hints)
            with_triggers = sum(1 for q in catalog.questions 
                               if q.gate_config and q.gate_config.context_triggers)
            
            print(f"   Fragen mit Slot-Config: {with_slots}")
            print(f"   Fragen mit Conversation-Hints: {with_hints}")
            print(f"   Fragen mit Keyword-Triggers: {with_triggers}")
            
            # Zeige einige Policies
            print(f"\n   Angewendete Policies (erste 5):")
            for policy in catalog.meta.policies_applied[:5]:
                print(f"     - {policy}")
        else:
            print(f"\n   Info: Policies deaktiviert")
        
        # Group by category
        categories = {}
        for q in catalog.questions:
            cat = q.category or "uncategorized"
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\nKategorien:")
        for cat, count in sorted(categories.items()):
            print(f"   - {cat}: {count}")
        
        # Show first 10 questions as preview
        print(f"\nPreview (erste 10 Fragen):")
        for q in catalog.questions[:10]:
            req_str = "[REQ]" if q.required else "[OPT]"
            tier = "T1" if q.id.startswith('pq_') else ("T2" if q.id.startswith('vc_') else "T3")
            print(f"   {req_str} [{tier}] {q.question[:70]}")
        
        # Offer to save
        save_path = Path("test_output") / f"questions_hybrid_test.json"
        save_path.parent.mkdir(exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(catalog.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"\nGespeichert: {save_path}")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\nFehler: {e}")
        import traceback
        traceback.print_exc()


def main():
    """CLI Entry Point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Question Generator mit lokaler Protocol-Datei")
    parser.add_argument("protocol_file", type=str, help="Pfad zur Gesprächsprotokoll JSON-Datei")
    parser.add_argument(
        "--policy-level",
        choices=["basic", "standard", "advanced", "none"],
        default="standard",
        help="Policy level (default: standard, none = disabled)"
    )
    
    args = parser.parse_args()
    
    policy_level = None if args.policy_level == "none" else args.policy_level
    
    # Run async
    asyncio.run(test_with_local_protocol(args.protocol_file, policy_level or "standard"))


if __name__ == "__main__":
    main()

