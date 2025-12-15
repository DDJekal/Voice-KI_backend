"""
Test Structure V2 Pipeline mit dem Protokoll vom User

Testet:
- Arbeitserlaubnis in Deutschland
- Examinierte Pflegefachkraft (zwingend)
- Deutsch B2
- Krankenpflegehelfer (alternativ)
- Gespraech per DU
"""

import asyncio
import json
import logging
from backend.src.questions.pipeline.extract_multistage import extract
from backend.src.questions.pipeline.structure_v2 import build_questions_v2

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test-Protokoll vom User
TEST_PROTOCOL = {
    "id": 1,
    "name": "Test Pflegefachkraft",
    "pages": [
        {
            "id": 1,
            "name": "Der Bewerber erfuellt folgende Kriterien:",
            "position": 1,
            "prompts": [
                {
                    "id": 1,
                    "question": "Arbeitserlaubnis in Deutschland?",
                    "position": 1
                },
                {
                    "id": 2,
                    "question": "zwingend: Examinierte Pflegefachkraft",
                    "position": 2
                },
                {
                    "id": 3,
                    "question": "Deutsch: B2",
                    "position": 3
                },
                {
                    "id": 4,
                    "question": "alternativ: 1-jaehrige Ausbildung zur Krankenpflegehelfer (m/w/d)",
                    "position": 4
                },
                {
                    "id": 5,
                    "question": "Gespraech per DU",
                    "position": 5
                }
            ]
        }
    ]
}


async def test_v2_pipeline():
    """Test die V2 Pipeline"""
    
    print("\n" + "=" * 70)
    print("TEST: Structure V2 Pipeline")
    print("=" * 70)
    
    # Stage 1: Extract
    print("\n[1] Extracting protocol data...")
    extract_result = await extract(TEST_PROTOCOL)
    
    print(f"\nExtraction Results:")
    print(f"  Must-Haves: {extract_result.must_have}")
    print(f"  Alternatives: {extract_result.alternatives}")
    print(f"  Protocol Questions: {len(extract_result.protocol_questions)}")
    
    # Stage 2-4: Build Questions V2
    print("\n[2] Building questions with V2 pipeline...")
    questions = build_questions_v2(extract_result)
    
    # Analyse Results
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("=" * 70)
    print(f"\nTotal Questions: {len(questions)}")
    
    # Gruppiere nach Kategorie
    by_category = {}
    gate_questions = []
    
    for q in questions:
        # Kategorie
        cat = q.metadata.get('category', 'unknown') if q.metadata else 'unknown'
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(q)
        
        # Gate Questions
        if q.gate_config and q.gate_config.is_gate:
            gate_questions.append(q)
    
    print(f"\nGate Questions: {len(gate_questions)}")
    for gq in gate_questions:
        print(f"  - [{gq.id}] {gq.question}")
        print(f"    Type: {gq.type}, Priority: {gq.priority}")
        if gq.metadata:
            print(f"    Source: {gq.metadata.get('source_text', 'N/A')}")
    
    print(f"\nBy Category:")
    for cat, qs in sorted(by_category.items()):
        print(f"  {cat}: {len(qs)} questions")
    
    # Check Coverage
    print("\n" + "=" * 70)
    print("COVERAGE CHECK:")
    print("=" * 70)
    
    criteria = {
        "Arbeitserlaubnis": False,
        "Examinierte Pflegefachkraft": False,
        "Deutsch B2": False,
        "Krankenpflegehelfer": False,
        "Gespraech per DU": False
    }
    
    for q in questions:
        q_text = q.question.lower()
        source = q.metadata.get('source_text', '').lower() if q.metadata else ''
        combined = q_text + " " + source
        
        if 'arbeitserlaubnis' in combined:
            criteria["Arbeitserlaubnis"] = True
        
        if 'examinierte' in combined or 'pflegefachkraft' in combined:
            criteria["Examinierte Pflegefachkraft"] = True
        
        if 'deutsch' in combined and ('b2' in combined or 'sprachkenntnisse' in combined):
            criteria["Deutsch B2"] = True
        
        if 'krankenpflegehelfer' in combined:
            criteria["Krankenpflegehelfer"] = True
        
        if 'du' in combined or 'per du' in combined or 'kommunikation' in combined:
            criteria["Gespraech per DU"] = True
    
    # Print Coverage
    all_covered = True
    for criterion, covered in criteria.items():
        status = "OK" if covered else "FEHLT"
        symbol = "[OK]" if covered else "[FEHLT]"
        print(f"  {symbol} {criterion}: {status}")
        if not covered:
            all_covered = False
    
    if all_covered:
        print("\n SUCCESS: Alle Kriterien wurden als Fragen generiert!")
    else:
        print("\n WARNING: Einige Kriterien fehlen!")
    
    # Output Full Questions
    print("\n" + "=" * 70)
    print("ALLE FRAGEN:")
    print("=" * 70)
    
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. [{q.id}] {q.question}")
        if q.preamble:
            print(f"   Preamble: {q.preamble}")
        print(f"   Type: {q.type}, Priority: {q.priority}, Group: {q.group}")
        if q.options:
            print(f"   Options: {q.options}")
        if q.gate_config:
            print(f"   Gate: {q.gate_config.is_gate}")
        if q.metadata:
            print(f"   Category: {q.metadata.get('category')}, Source: {q.metadata.get('source_type')}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(test_v2_pipeline())

