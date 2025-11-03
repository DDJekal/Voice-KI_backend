"""Batch-Verarbeitung aller Bewerber mit Status 'Neu intern'"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.data_sources.api_loader import APIDataSource
from src.telephony.webrtc_client import WebRTCConversation
from src.orchestrator.call_orchestrator import CallOrchestrator


def process_all_applicants():
    """
    Verarbeitet alle Bewerber mit Status 'Neu intern'.
    
    Startet für jeden Bewerber einen Call mit den zugehörigen
    Unternehmens- und Kampagnendaten.
    """
    
    settings = get_settings()
    
    print("="*70)
    print("BATCH-VERARBEITUNG: Alle Bewerber mit Status 'Neu intern'")
    print("="*70)
    
    # Prüfe ob API Source aktiviert ist
    if not settings.use_api_source:
        print("\n❌ Fehler: USE_API_SOURCE muss auf 'true' gesetzt sein!")
        print("   Setze in .env: USE_API_SOURCE=true")
        sys.exit(1)
    
    if not settings.api_url:
        print("\n❌ Fehler: API_URL nicht gesetzt!")
        print("   Setze in .env: API_URL=https://your-api-url.com")
        sys.exit(1)
    
    try:
        # API Data Source
        print(f"\n📡 Verbinde zu API: {settings.api_url}")
        print(f"   Status: {settings.api_status}")
        print(f"   Test-Filter: {'Aktiv' if settings.filter_test_applicants else 'Deaktiviert'}")
        
        api = APIDataSource(
            api_url=settings.api_url,
            api_key=settings.api_key,
            status=settings.api_status,
            filter_test_applicants=settings.filter_test_applicants
        )
        
        # Conversation Client
        conversation_client = WebRTCConversation(
            api_key=settings.elevenlabs_api_key,
            base_url="https://api.eu.residency.elevenlabs.io"
        )
        
        # Orchestrator
        orchestrator = CallOrchestrator(
            data_source=api,
            conversation_client=conversation_client,
            settings=settings
        )
        
        # Alle Bewerber holen
        print("\n📋 Lade Bewerber-Liste...")
        applicants = api.list_pending_applicants()
        
        if not applicants:
            print("\n⚠️  Keine Bewerber mit Status 'Neu intern' gefunden.")
            return
        
        print(f"\n✅ {len(applicants)} Bewerber gefunden\n")
        print("="*70)
        
        # Statistik
        successful = 0
        failed = 0
        errors = []
        
        # Verarbeite jeden Bewerber
        for i, applicant in enumerate(applicants, 1):
            name = f"{applicant['first_name']} {applicant['last_name']}"
            phone = applicant['telephone']
            campaign_id = str(applicant['campaign_id'])
            
            print(f"\n[{i}/{len(applicants)}] Verarbeite: {name}")
            print(f"             Telefon: {phone}")
            print(f"             Campaign ID: {campaign_id}")
            
            try:
                result = orchestrator.start_call(
                    applicant_id=phone,
                    campaign_id=campaign_id
                )
                
                print(f"   ✅ Call gestartet: {result['conversation_id']}")
                successful += 1
                
            except Exception as e:
                print(f"   ❌ Fehler: {e}")
                failed += 1
                errors.append({
                    "applicant": name,
                    "phone": phone,
                    "error": str(e)
                })
        
        # Zusammenfassung
        print("\n" + "="*70)
        print("ZUSAMMENFASSUNG")
        print("="*70)
        print(f"✅ Erfolgreich: {successful}")
        print(f"❌ Fehlgeschlagen: {failed}")
        print(f"📊 Gesamt: {len(applicants)}")
        
        if errors:
            print("\n❌ FEHLER-DETAILS:")
            for err in errors:
                print(f"\n  Bewerber: {err['applicant']}")
                print(f"  Telefon: {err['phone']}")
                print(f"  Fehler: {err['error']}")
        
        print("\n" + "="*70)
        print("✅ Batch-Verarbeitung abgeschlossen!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ KRITISCHER FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    process_all_applicants()

