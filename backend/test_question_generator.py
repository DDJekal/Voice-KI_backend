"""
Test Script für Question Generator

Testet die automatische Generierung von questions.json aus Gesprächsprotokollen.
"""

import sys
import asyncio
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.data_sources.api_loader import APIDataSource
from src.questions.builder import build_question_catalog


async def test_question_generator(campaign_id: str, policy_level: str = "standard"):
    """
    Testet Question Generator mit einer Campaign.
    
    Args:
        campaign_id: Campaign ID zum Testen
        policy_level: Policy level zum Testen (basic, standard, advanced)
    """
    print("\n" + "="*70)
    print("🧪 TEST: Question Generator")
    print("="*70)
    print(f"Campaign ID: {campaign_id}")
    print(f"Policy Level: {policy_level}")
    print("="*70 + "\n")
    
    try:
        # Config laden
        settings = get_settings()
        
        if not settings.openai_api_key:
            print("❌ Fehler: OPENAI_API_KEY nicht gesetzt!")
            print("   Setze in .env: OPENAI_API_KEY=sk-...")
            return
        
        print(f"✅ OpenAI API Key: {settings.openai_api_key[:20]}...")
        print(f"✅ OpenAI Model: {settings.openai_model}")
        
        # API Data Source
        print("\n📡 Initialisiere API Data Source...")
        api = APIDataSource(
            api_url=settings.api_url,
            api_key=settings.api_key,
            status="new",
            filter_test_applicants=True
        )
        
        # Lade Protocol
        print(f"\n📥 Lade Conversation Protocol für Campaign {campaign_id}...")
        protocol = api.get_conversation_protocol(campaign_id)
        
        print(f"   ✅ Protocol: {protocol.get('name', 'Unknown')}")
        print(f"   ✅ Pages: {len(protocol.get('pages', []))}")
        
        # Generiere Questions
        print("\n🤖 Generiere questions.json mit OpenAI...")
        print(f"   Policy Level: {policy_level}")
        print("   (Dies kann 10-30 Sekunden dauern...)")
        
        context = {"policy_level": policy_level}
        catalog = await build_question_catalog(protocol, context)
        
        # Ergebnisse anzeigen
        print("\n" + "="*70)
        print("✅ QUESTION CATALOG ERFOLGREICH GENERIERT!")
        print("="*70)
        
        print(f"\n📊 Statistiken:")
        print(f"   Total Questions: {len(catalog.questions)}")
        print(f"   Required: {sum(1 for q in catalog.questions if q.required)}")
        print(f"   Optional: {sum(1 for q in catalog.questions if not q.required)}")
        
        # NEU: Policy stats
        if catalog._meta.policies_applied:
            print(f"\n🔧 Policy-Enhancements:")
            print(f"   Policies angewendet: {len(catalog._meta.policies_applied)}")
            
            with_slots = sum(1 for q in catalog.questions if q.slot_config)
            with_hints = sum(1 for q in catalog.questions if q.conversation_hints)
            with_triggers = sum(1 for q in catalog.questions 
                               if q.gate_config and q.gate_config.context_triggers)
            
            print(f"   Fragen mit Slot-Config: {with_slots}")
            print(f"   Fragen mit Conversation-Hints: {with_hints}")
            print(f"   Fragen mit Keyword-Triggers: {with_triggers}")
            
            # Zeige einige Policies
            print(f"\n   Angewendete Policies (erste 5):")
            for policy in catalog._meta.policies_applied[:5]:
                print(f"     - {policy}")
        else:
            print(f"\n   ℹ️  Policies deaktiviert")
        
        # Group by category
        categories = {}
        for q in catalog.questions:
            cat = q.category or "uncategorized"
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n📦 Kategorien:")
        for cat, count in sorted(categories.items()):
            print(f"   - {cat}: {count}")
        
        # Show first 5 questions as preview
        print(f"\n📝 Preview (erste 5 Fragen):")
        for q in catalog.questions[:5]:
            req_str = "✓" if q.required else "○"
            print(f"   {req_str} [{q.id}] {q.question}")
        
        # Offer to save
        save_path = Path("test_output") / f"questions_{campaign_id}.json"
        save_path.parent.mkdir(exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(catalog.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Gespeichert: {save_path}")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()


def main():
    """CLI Entry Point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Question Generator mit Policies")
    parser.add_argument("campaign_id", type=str, help="Campaign ID zum Testen")
    parser.add_argument(
        "--policy-level",
        choices=["basic", "standard", "advanced", "none"],
        default="standard",
        help="Policy level (default: standard, none = disabled)"
    )
    
    args = parser.parse_args()
    
    policy_level = None if args.policy_level == "none" else args.policy_level
    
    # Run async
    asyncio.run(test_question_generator(args.campaign_id, policy_level or "standard"))


if __name__ == "__main__":
    main()

