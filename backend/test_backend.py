"""
Test-Script für VoiceKI Backend
Testet die Implementierung mit Beispieldaten im Dry-Run Mode
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from src.config import Settings
from src.data_sources.file_loader import FileDataSource
from src.aggregator.unified_aggregator import UnifiedAggregator
from src.aggregator.knowledge_base_builder import KnowledgeBaseBuilder
from src.elevenlabs.voice_client import MockElevenLabsClient
from src.orchestrator.call_orchestrator import CallOrchestrator


def test_data_loading():
    """Test 1: Daten aus Files laden"""
    print("\n" + "="*70)
    print("TEST 1: Data Loading")
    print("="*70)
    
    data_dir = "../KI-Sellcruiting_VerarbeitungProtokollzuFragen/Input_datein_beispiele"
    data_source = FileDataSource(data_dir)
    
    # Test Applicant Profile
    applicant = data_source.get_applicant_profile("test")
    print(f"✓ Applicant geladen: {applicant.get('first_name')} {applicant.get('last_name')}")
    
    # Test Address
    address = data_source.get_applicant_address("test")
    print(f"✓ Address geladen: {address.get('city', 'N/A')}")
    
    # Test Company
    company = data_source.get_company_profile("test")
    print(f"✓ Company geladen: {company.get('name', 'N/A')}")
    
    # Test Protocol
    protocol = data_source.get_conversation_protocol("test")
    print(f"✓ Protocol geladen: {len(protocol.get('pages', []))} Seiten")
    
    return applicant, address, company, protocol


def test_aggregation(applicant, address, company):
    """Test 2: Datenaggregation"""
    print("\n" + "="*70)
    print("TEST 2: Data Aggregation")
    print("="*70)
    
    aggregator = UnifiedAggregator()
    
    # Phase 1
    phase1 = aggregator.aggregate_phase_1(applicant, address)
    print(f"✓ Phase 1: {len(phase1)} Variablen")
    print(f"  - Bewerber: {phase1['candidatefirst_name']} {phase1['candidatelast_name']}")
    print(f"  - Stadt: {phase1['city']}")
    
    # Phase 2
    phase2 = aggregator.aggregate_phase_2(company)
    print(f"✓ Phase 2: {len(phase2)} Variablen")
    print(f"  - Unternehmen: {phase2['companyname']}")
    
    # Phase 3 (mit Dummy questions.json)
    dummy_questions = {
        "_meta": {},
        "questions": [
            {"id": "test1", "question": "Test", "type": "boolean", "required": True, "priority": 1}
        ]
    }
    phase3 = aggregator.aggregate_phase_3(dummy_questions)
    print(f"✓ Phase 3: {phase3['total_questions']} Fragen")
    
    # Phase 4
    phase4 = aggregator.aggregate_phase_4(applicant)
    print(f"✓ Phase 4: {len(phase4)} Variablen")
    
    return phase1, phase2, phase3, phase4


def test_knowledge_base(phase1, phase2, phase3, phase4):
    """Test 3: Knowledge Base Builder"""
    print("\n" + "="*70)
    print("TEST 3: Knowledge Base Builder")
    print("="*70)
    
    kb_builder = KnowledgeBaseBuilder()
    
    kb1 = kb_builder.build_phase_1(phase1)
    print(f"✓ Phase 1 KB: {len(kb1)} Zeichen")
    
    kb2 = kb_builder.build_phase_2(phase2)
    print(f"✓ Phase 2 KB: {len(kb2)} Zeichen")
    
    kb3 = kb_builder.build_phase_3({"questions": phase3["questions"]})
    print(f"✓ Phase 3 KB: {len(kb3)} Zeichen")
    
    kb4 = kb_builder.build_phase_4(phase4)
    print(f"✓ Phase 4 KB: {len(kb4)} Zeichen")
    
    # Preview
    print(f"\n📝 Phase 1 KB Preview (erste 300 Zeichen):")
    print(kb1[:300] + "...")
    
    return kb1, kb2, kb3, kb4


def test_elevenlabs_mock():
    """Test 4: ElevenLabs Mock Client"""
    print("\n" + "="*70)
    print("TEST 4: ElevenLabs Mock Client")
    print("="*70)
    
    client = MockElevenLabsClient()
    
    result = client.start_conversation(
        agent_id="test_agent",
        knowledge_base="Test Knowledge Base Content"
    )
    
    print(f"✓ Conversation gestartet: {result['conversation_id']}")
    print(f"✓ Status: {result['status']}")
    
    # Status abrufen
    status = client.get_conversation_status(result['conversation_id'])
    print(f"✓ Status abgerufen: {status['status']}")
    
    # Transcript abrufen
    transcript = client.get_transcript(result['conversation_id'])
    print(f"✓ Transcript: {transcript[:50]}...")
    
    return result


def test_full_orchestration():
    """Test 5: Kompletter Orchestrator"""
    print("\n" + "="*70)
    print("TEST 5: Full Orchestration")
    print("="*70)
    
    # Settings
    settings = Settings(
        data_dir="../KI-Sellcruiting_VerarbeitungProtokollzuFragen/Input_datein_beispiele",
        questions_json_path="../KI-Sellcruiting_VerarbeitungProtokollzuFragen/output/questions.json",
        typescript_tool_path="../KI-Sellcruiting_VerarbeitungProtokollzuFragen",
        prompts_dir="../VoiceKI _prompts",
        generate_questions=False,
        dry_run=True,
        elevenlabs_api_key="mock",
        elevenlabs_agent_id="mock"
    )
    
    # Components
    data_source = FileDataSource(settings.data_dir)
    elevenlabs_client = MockElevenLabsClient()
    
    # Orchestrator
    orchestrator = CallOrchestrator(
        data_source=data_source,
        elevenlabs_client=elevenlabs_client,
        settings=settings
    )
    
    # Start Call
    result = orchestrator.start_call(
        applicant_id="test123",
        campaign_id="campaign456"
    )
    
    print(f"\n✓ Call erfolgreich orchestriert!")
    print(f"  - Conversation ID: {result['conversation_id']}")
    print(f"  - Status: {result['status']}")
    print(f"  - Phasen: {result.get('phases', 'N/A')}")
    print(f"  - KB Size: {result.get('knowledge_base_size', 0)} Zeichen")
    
    return result


def main():
    """Haupttest-Funktion"""
    print("\n" + "="*70)
    print("🧪 VoiceKI Backend - Integration Tests")
    print("="*70)
    
    try:
        # Test 1: Data Loading
        applicant, address, company, protocol = test_data_loading()
        
        # Test 2: Aggregation
        phase1, phase2, phase3, phase4 = test_aggregation(applicant, address, company)
        
        # Test 3: Knowledge Base
        kb1, kb2, kb3, kb4 = test_knowledge_base(phase1, phase2, phase3, phase4)
        
        # Test 4: ElevenLabs Mock
        elevenlabs_result = test_elevenlabs_mock()
        
        # Test 5: Full Orchestration
        final_result = test_full_orchestration()
        
        # Summary
        print("\n" + "="*70)
        print("✅ ALLE TESTS BESTANDEN!")
        print("="*70)
        print("\n💡 Nächste Schritte:")
        print("   1. .env Datei erstellen (siehe backend/.env.example)")
        print("   2. ElevenLabs API Key eintragen")
        print("   3. Test ohne --dry-run:")
        print("      python main.py --applicant-id test --campaign-id test")
        print("\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FEHLGESCHLAGEN: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

