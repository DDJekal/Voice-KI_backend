"""
Debug Test für Campaign 909 - Repliziert HOC Request lokal
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from src.questions.builder import build_question_catalog

# WICHTIG: Echtes Protokoll von Campaign 909 hier einfügen
# Du kannst es von HOC Django exportieren oder aus der DB holen
test_protocol_909 = {
    "id": 909,
    "name": "Campaign 909 Protocol",
    "pages": [
        # HIER ECHTES PROTOKOLL EINFÜGEN
        {
            "id": 1,
            "name": "Testpage",
            "position": 1,
            "prompts": [
                {
                    "id": 1,
                    "question": "Test Question",
                    "position": 1
                }
            ]
        }
    ]
}

async def main():
    print("=" * 70)
    print("LOCAL DEBUG TEST - Campaign 909")
    print("=" * 70)
    
    try:
        print("\n1. Building Question Catalog...")
        context = {"policy_level": "standard"}
        catalog = await build_question_catalog(test_protocol_909, context)
        
        print(f"\n2. SUCCESS! Generated {len(catalog.questions)} questions")
        
        print("\n3. Catalog has following attributes:")
        print(f"   - questions: {hasattr(catalog, 'questions')}")
        print(f"   - meta: {hasattr(catalog, 'meta')}")
        print(f"   - knowledge_base: {hasattr(catalog, 'knowledge_base')}")
        
        print("\n4. Simulating webhook response...")
        # Simuliere was api_server.py macht
        trimmed_questions = []
        for q in catalog.questions:
            try:
                q_dict = q.model_dump()
                # Nur export fields
                trimmed = {k: q_dict.get(k) for k in ['id', 'question', 'type', 'required', 'priority', 'group']}
                trimmed_questions.append(trimmed)
            except Exception as e:
                print(f"   ERROR trimming question: {e}")
        
        print(f"   Trimmed {len(trimmed_questions)} questions")
        
        # Simuliere Response Objekt
        response_dict = {
            "protocol_id": 909,
            "protocol_name": "Test",
            "processed_at": "2025-12-15T15:00:00Z",
            "question_count": len(trimmed_questions),
            "questions": trimmed_questions
        }
        
        print("\n5. Response Keys:")
        print(f"   {list(response_dict.keys())}")
        
        print("\n6. Has 'questions' key?")
        if 'questions' in response_dict:
            print("   YES - HOC sollte funktionieren!")
        else:
            print("   NO - HOC wird crashen!")
        
    except Exception as e:
        print(f"\nEXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    # Read debug log
    debug_log = Path(r'c:\Users\David Jekal\Desktop\Projekte\KI-Sellcrtuiting_VoiceKI\.cursor\debug.log')
    if debug_log.exists():
        print("\n" + "=" * 70)
        print("DEBUG LOG:")
        print("=" * 70)
        with open(debug_log) as f:
            for line in f:
                try:
                    log = json.loads(line)
                    print(f"[{log['location']}] {log['message']}: {log.get('data', {})}")
                except:
                    print(line.strip())

if __name__ == "__main__":
    asyncio.run(main())

