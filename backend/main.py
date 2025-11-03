"""
VoiceKI Backend - CLI Entry Point

Standalone Orchestrator für ElevenLabs Voice-Recruiting-Calls.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.data_sources.file_loader import FileDataSource
from src.data_sources.api_loader import APIDataSource
from src.elevenlabs.voice_client import ElevenLabsVoiceClient, MockElevenLabsClient
from src.orchestrator.call_orchestrator import CallOrchestrator


def main():
    """CLI Entry Point"""
    
    parser = argparse.ArgumentParser(
        description="VoiceKI Backend - ElevenLabs Voice Recruiting Orchestrator"
    )
    
    parser.add_argument(
        "--applicant-id",
        type=str,
        required=True,
        help="Bewerber-ID (für FileLoader: beliebiger String)"
    )
    
    parser.add_argument(
        "--campaign-id",
        type=str,
        required=True,
        help="Kampagnen-ID (für FileLoader: beliebiger String)"
    )
    
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3, 4],
        help="Nur bestimmte Phase starten (1-4)"
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        help="Überschreibt DATA_DIR aus .env"
    )
    
    parser.add_argument(
        "--generate-questions",
        action="store_true",
        help="Führt TypeScript Tool aus um questions.json zu generieren"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mock-Modus: Kein echter ElevenLabs Call"
    )
    
    args = parser.parse_args()
    
    # Lade Konfiguration
    settings = get_settings()
    
    # Override Settings aus CLI
    if args.data_dir:
        settings.data_dir = args.data_dir
    if args.generate_questions:
        settings.generate_questions = True
    if args.dry_run:
        settings.dry_run = True
    
    print("\n" + "="*70)
    print("🎙️  VoiceKI Backend - Voice Recruiting Orchestrator")
    print("="*70)
    print(f"Modus: {'DRY-RUN (Mock)' if settings.dry_run else 'PRODUCTION'}")
    print("="*70 + "\n")
    
    try:
        # Initialisiere Data Source
        if settings.use_api_source:
            print("ℹ️  Verwende API Data Source")
            print(f"   API URL: {settings.api_url}")
            print(f"   Status: {settings.api_status}")
            print(f"   Test-Filter: {'Aktiv' if settings.filter_test_applicants else 'Deaktiviert'}")
            
            if not settings.api_url:
                print("❌ Fehler: API_URL nicht gesetzt!")
                print("   Bitte .env Datei prüfen")
                sys.exit(1)
            
            data_source = APIDataSource(
                api_url=settings.api_url,
                api_key=settings.api_key,
                status=settings.api_status,
                filter_test_applicants=settings.filter_test_applicants
            )
        else:
            print("ℹ️  Verwende File Data Source")
            print(f"   Data Dir: {settings.data_dir}")
            data_source = FileDataSource(settings.data_dir)
        
        # Initialisiere ElevenLabs Client
        if settings.dry_run:
            print("ℹ️  Verwende Mock-Client (kein echter API Call)\n")
            elevenlabs_client = MockElevenLabsClient()
        else:
            if not settings.elevenlabs_api_key:
                print("❌ Fehler: ELEVENLABS_API_KEY nicht gesetzt!")
                print("   Bitte .env Datei erstellen (siehe .env.example)")
                sys.exit(1)
            
            elevenlabs_client = ElevenLabsVoiceClient(
                api_key=settings.elevenlabs_api_key
            )
        
        # Initialisiere Orchestrator
        orchestrator = CallOrchestrator(
            data_source=data_source,
            elevenlabs_client=elevenlabs_client,
            settings=settings
        )
        
        # Starte Call
        result = orchestrator.start_call(
            applicant_id=args.applicant_id,
            campaign_id=args.campaign_id,
            phase=args.phase
        )
        
        # Ausgabe
        print("\n" + "="*70)
        print("📊 ERGEBNIS")
        print("="*70)
        print(f"Conversation ID: {result.get('conversation_id')}")
        print(f"Status: {result.get('status')}")
        if 'phases' in result:
            print(f"Phasen: {result['phases']}")
        if 'knowledge_base_size' in result:
            print(f"Knowledge Base: {result['knowledge_base_size']} Zeichen")
        print("="*70 + "\n")
        
        if not settings.dry_run:
            print("💡 Tipp: Verwende --dry-run für Tests ohne echte API-Calls\n")
        
        sys.exit(0)
        
    except FileNotFoundError as e:
        print(f"\n❌ Fehler: Datei nicht gefunden")
        print(f"   {e}")
        print(f"\n💡 Tipp: Prüfe DATA_DIR in .env oder --data-dir Parameter")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

