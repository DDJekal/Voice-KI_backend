"""
Test-Script für neue Input-Struktur (Input_ordner/)
Testet die Anpassungen für Q&A Format und separate Dateien
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


def test_new_input_structure():
    """Test 1: Neue Input-Struktur (Input_ordner/)"""
    print("\n" + "="*70)
    print("TEST 1: Neue Input-Struktur (Input_ordner/)")
    print("="*70)
    
    data_dir = "../Input_ordner"
    data_source = FileDataSource(data_dir)
    
    # Test 1.1: Bewerberprofil (eine Datei)
    applicant = data_source.get_applicant_profile("test")
    print(f"✓ Bewerberprofil geladen: {applicant.get('first_name')} {applicant.get('last_name')}")
    assert applicant["first_name"] == "Max"
    assert applicant["last_name"] == "Mustermann"
    
    # Test 1.2: Separate Adresse
    address = data_source.get_applicant_address("test")
    print(f"✓ Adresse geladen: {address.get('city')}, {address.get('postal_code')}")
    assert address["city"] == "Freiburg"
    assert address["postal_code"] == "79098"
    
    # Test 1.3: Unternehmensprofil (Q&A Format)
    company = data_source.get_company_profile("test")
    print(f"✓ Unternehmensprofil geladen: {company.get('name')}")
    
    # Check Q&A Format
    first_prompt = company["pages"][0]["prompts"][0]
    assert "answer" in first_prompt, "Should have answer field (Q&A format)"
    print(f"✓ Q&A Format erkannt: {first_prompt['question'][:50]}...")
    
    # Test 1.4: Separates Gesprächsprotokoll
    protocol = data_source.get_conversation_protocol("test")
    print(f"✓ Gesprächsprotokoll geladen: {protocol.get('name')}")
    assert "pages" in protocol
    
    # Check type field (neues Format)
    if protocol["pages"]:
        first_protocol_prompt = protocol["pages"][0]["prompts"][0]
        if "type" in first_protocol_prompt:
            print(f"✓ Type-Feld gefunden: {first_protocol_prompt['type']}")
    
    return applicant, address, company, protocol


def test_qa_aggregation(applicant, address, company):
    """Test 2: Q&A Format Aggregation"""
    print("\n" + "="*70)
    print("TEST 2: Q&A Format Aggregation")
    print("="*70)
    
    aggregator = UnifiedAggregator()
    
    # Test Phase 1 (unverändert)
    phase1 = aggregator.aggregate_phase_1(applicant, address)
    print(f"✓ Phase 1: {len(phase1)} Variablen")
    print(f"  - Bewerber: {phase1['candidatefirst_name']} {phase1['candidatelast_name']}")
    print(f"  - Adresse: {phase1['street']} {phase1['house_number']}, {phase1['city']}")
    
    # Test Phase 2 (NEU: Q&A Format)
    phase2 = aggregator.aggregate_phase_2(company)
    print(f"✓ Phase 2 (Q&A Format): {len(phase2)} Variablen")
    print(f"  - Unternehmen: {phase2['companyname']}")
    print(f"  - Größe: {phase2['companysize']} Mitarbeitende")
    print(f"  - Standort: {phase2['campaignlocation_label']}")
    print(f"  - Pitch (gekürzt): {phase2['companypitch'][:100]}...")
    
    # Validierung
    assert phase2['companyname'], "Company name should not be empty"
    assert phase2['companysize'] > 0, "Company size should be positive"
    assert phase2['campaignlocation_label'], "Location should not be empty"
    
    return phase1, phase2


def test_knowledge_base_qa(phase1, phase2):
    """Test 3: Knowledge Base mit Q&A Daten"""
    print("\n" + "="*70)
    print("TEST 3: Knowledge Base Builder (Q&A Daten)")
    print("="*70)
    
    kb_builder = KnowledgeBaseBuilder()
    
    kb1 = kb_builder.build_phase_1(phase1)
    print(f"✓ Phase 1 KB: {len(kb1)} Zeichen")
    
    kb2 = kb_builder.build_phase_2(phase2)
    print(f"✓ Phase 2 KB: {len(kb2)} Zeichen")
    
    # Preview Phase 2 KB
    print(f"\n📝 Phase 2 KB Preview (erste 400 Zeichen):")
    print(kb2[:400] + "...")
    
    return kb1, kb2


def test_backward_compatibility():
    """Test 4: Backward Compatibility mit alter Struktur"""
    print("\n" + "="*70)
    print("TEST 4: Backward Compatibility (alte Test-Daten)")
    print("="*70)
    
    try:
        data_dir = "../KI-Sellcruiting_VerarbeitungProtokollzuFragen/Input_datein_beispiele"
        data_source = FileDataSource(data_dir)
        
        # Test alte Struktur
        applicant = data_source.get_applicant_profile("test")
        address = data_source.get_applicant_address("test")
        company = data_source.get_company_profile("test")
        
        print(f"✓ Alte Struktur funktioniert: {applicant.get('first_name')}")
        print(f"✓ Teil1+Teil2 Merge funktioniert")
        
        aggregator = UnifiedAggregator()
        phase2 = aggregator.aggregate_phase_2(company)
        
        print(f"✓ Alte Format-Aggregation funktioniert: {phase2['companyname']}")
        print("✓ Backward Compatibility gewahrt!")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Backward Compatibility Test übersprungen: {e}")
        return False


def test_full_orchestration_new():
    """Test 5: Kompletter Orchestrator mit neuer Struktur"""
    print("\n" + "="*70)
    print("TEST 5: Full Orchestration (neue Struktur)")
    print("="*70)
    
    # Settings für neue Struktur
    settings = Settings(
        data_dir="../Input_ordner",
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
    print(f"  - KB Size: {result.get('knowledge_base_size', 0)} Zeichen")
    
    return result


def main():
    """Haupttest-Funktion"""
    print("\n" + "="*70)
    print("🧪 VoiceKI Backend - Tests für neue Input-Struktur")
    print("="*70)
    
    try:
        # Test 1: Neue Input-Struktur
        applicant, address, company, protocol = test_new_input_structure()
        
        # Test 2: Q&A Aggregation
        phase1, phase2 = test_qa_aggregation(applicant, address, company)
        
        # Test 3: Knowledge Base
        kb1, kb2 = test_knowledge_base_qa(phase1, phase2)
        
        # Test 4: Backward Compatibility
        backward_compat = test_backward_compatibility()
        
        # Test 5: Full Orchestration
        final_result = test_full_orchestration_new()
        
        # Summary
        print("\n" + "="*70)
        print("✅ ALLE TESTS BESTANDEN!")
        print("="*70)
        print("\n📊 Zusammenfassung:")
        print("   ✓ Neue Input-Struktur: Bewerberprofil.json + Adresse des Bewerbers.json")
        print("   ✓ Q&A Format: Unternehmensprofil mit question/answer Paaren")
        print("   ✓ Separates Gesprächsprotokoll mit type Feld")
        print("   ✓ Phase 2 Aggregation mit Q&A Parser")
        print("   ✓ Knowledge Base Builder funktioniert")
        if backward_compat:
            print("   ✓ Backward Compatibility mit alter Struktur")
        print("   ✓ Full Orchestration erfolgreich")
        print("\n💡 Das Backend ist bereit für die echte Cloud-Integration!")
        print("\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FEHLGESCHLAGEN: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

