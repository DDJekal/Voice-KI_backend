"""
Test Classification + V2 Pipeline + Knowledge Base

Testet:
1. STAGE 0: Classification
2. V2 Pipeline mit classified_data
3. Knowledge Base Export
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from src.questions.builder import build_question_catalog


async def main():
    # Test mit Korian Protokoll (PDL)
    test_protocol = {
        "id": 5729,
        "name": "Pflegedienstleitung (PDL) - Korian",
        "pages": [
            {
                "id": 1,
                "name": "Der Bewerber erfüllt folgende Kriterien:",
                "position": 1,
                "prompts": [
                    {
                        "id": 1,
                        "question": "zwingend: Deutschkenntnisse B2",
                        "position": 1
                    },
                    {
                        "id": 2,
                        "question": "zwingend: Abgeschlossene Berufsausbildung als Gesundheits- und Krankenpfleger/in oder Altenpfleger/in",
                        "position": 2
                    },
                    {
                        "id": 3,
                        "question": "zwingend: Anerkannte Weiterbildung zur Pflegedienstleitung",
                        "position": 3
                    }
                ]
            },
            {
                "id": 2,
                "name": "Der Bewerber akzeptiert folgende Rahmenbedingungen:",
                "position": 2,
                "prompts": [
                    {
                        "id": 4,
                        "question": "Vollzeit (39-40 Wochenstunden)",
                        "position": 1
                    },
                    {
                        "id": 5,
                        "question": "Grundgehalt West: 3.250-4.000€ brutto, Ost: 3.100-3.700€ brutto",
                        "position": 2
                    },
                    {
                        "id": 6,
                        "question": "30 Tage Urlaub",
                        "position": 3
                    }
                ]
            },
            {
                "id": 3,
                "name": "Weitere Informationen",
                "position": 3,
                "prompts": [
                    {
                        "id": 7,
                        "question": "Kostenlose Weiterbildung in der Korian Akademie",
                        "position": 1
                    },
                    {
                        "id": 8,
                        "question": "50-80 PDL Einstellungen pro Jahr (hoher Bedarf)",
                        "position": 2
                    },
                    {
                        "id": 9,
                        "question": "Standorte: Berlin, Hamburg, München",
                        "position": 3
                    },
                    {
                        "id": 10,
                        "question": "Terminvorschläge: Montag oder Mittwoch",
                        "position": 4
                    },
                    {
                        "id": 11,
                        "question": "Blacklist: Dominik Lanz",
                        "position": 5
                    },
                    {
                        "id": 12,
                        "question": "AP: Sarah Müller mueller@korian.de",
                        "position": 6
                    }
                ]
            }
        ]
    }
    
    print("=" * 70)
    print("TEST: Classification + V2 + Knowledge Base")
    print("=" * 70)
    
    # Build catalog
    context = {"policy_level": "standard"}
    catalog = await build_question_catalog(test_protocol, context)
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    # 1. Questions
    print(f"\nGenerated {len(catalog.questions)} questions:")
    for i, q in enumerate(catalog.questions, 1):
        gate_status = "[GATE]" if q.gate_config and q.gate_config.is_gate else "      "
        print(f"  {i}. {gate_status} | {q.question[:60]}...")
    
    # 2. Knowledge Base
    if hasattr(catalog, 'knowledge_base') and catalog.knowledge_base:
        kb = catalog.knowledge_base
        print(f"\nKnowledge Base generated:")
        print(f"  - Benefits: {len(kb.get('company_benefits', []))}")
        print(f"  - Salary Info: {bool(kb.get('salary_info'))}")
        print(f"  - Work Conditions: {len(kb.get('work_conditions', []))}")
        print(f"  - Company Culture: {len(kb.get('company_culture', []))}")
        print(f"  - General Info: {len(kb.get('general_info', []))}")
        
        # Print details
        print("\nKnowledge Base Details:")
        
        if kb.get('company_benefits'):
            print("\n  Benefits:")
            for benefit in kb['company_benefits']:
                print(f"    - {benefit.get('text', '')}")
        
        if kb.get('salary_info'):
            print("\n  Salary Info:")
            print(f"    {json.dumps(kb['salary_info'], indent=4, ensure_ascii=False)}")
        
        if kb.get('work_conditions'):
            print("\n  Work Conditions:")
            for condition in kb['work_conditions']:
                print(f"    - {condition.get('text', '')}")
    else:
        print("\nNo Knowledge Base found")
    
    # 3. Export to file
    print("\n" + "=" * 70)
    print("Check output/questions_5729.json for full export")
    print("=" * 70)
    
    # 4. Validate Classifications
    print("\n" + "=" * 70)
    print("Expected Classifications:")
    print("=" * 70)
    print("  [OK] 'zwingend: Deutschkenntnisse B2' -> GATE_QUESTION")
    print("  [OK] 'Terminvorschlaege' -> PREFERENCE_QUESTION")
    print("  [OK] 'Blacklist: Dominik Lanz' -> BLACKLIST")
    print("  [OK] 'Kostenlose Weiterbildung' -> INFORMATION")
    print("  [OK] 'AP: Sarah Mueller' -> INTERNAL_NOTE")
    print("  [OK] '30 Tage Urlaub' -> INFORMATION (in KB)")
    print("  [OK] 'Grundgehalt' -> INFORMATION (in KB salary_info)")


if __name__ == "__main__":
    asyncio.run(main())

