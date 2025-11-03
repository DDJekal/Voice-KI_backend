"""
Campaign Setup Tool - Phase 1 des 2-Phasen WebRTC Link Systems

Erstellt einmalig pro Campaign ein wiederverwendbares Package mit KB Templates.
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.data_sources.api_loader import APIDataSource
from src.campaign.package_builder import CampaignPackageBuilder
from src.storage.campaign_storage import CampaignStorage


def setup_campaign(campaign_id: str, force: bool = False):
    """
    Erstellt Campaign Package und speichert lokal.
    
    Args:
        campaign_id: Campaign ID
        force: Überschreibt existierendes Package
    """
    
    print("\n" + "="*70)
    print("🔧 CAMPAIGN SETUP - Phase 1")
    print("="*70)
    print(f"Campaign ID: {campaign_id}")
    print("="*70 + "\n")
    
    # Konfiguration laden
    settings = get_settings()
    
    # Storage initialisieren
    storage = CampaignStorage()
    
    # Prüfe ob Package bereits existiert
    if storage.package_exists(campaign_id) and not force:
        print(f"⚠️  Campaign Package existiert bereits: {campaign_id}")
        print(f"   Nutze --force um zu überschreiben")
        
        info = storage.get_package_info(campaign_id)
        if info:
            print(f"\n📦 Existierendes Package:")
            print(f"   Company: {info['company_name']}")
            print(f"   Campaign: {info['campaign_name']}")
            print(f"   Erstellt: {info['created_at']}")
            print(f"   Fragen: {info['question_count']}")
        
        sys.exit(0)
    
    try:
        # API Data Source initialisieren
        print("📡 Initialisiere API Data Source...")
        
        if not settings.use_api_source:
            print("❌ Fehler: USE_API_SOURCE muss auf 'true' gesetzt sein!")
            print("   Setze in .env: USE_API_SOURCE=true")
            sys.exit(1)
        
        if not settings.api_url:
            print("❌ Fehler: API_URL nicht gesetzt!")
            print("   Setze in .env: API_URL=https://high-office.hirings.cloud/api/v1")
            sys.exit(1)
        
        api = APIDataSource(
            api_url=settings.api_url,
            api_key=settings.api_key,
            status="new",
            filter_test_applicants=True
        )
        print(f"   ✅ API URL: {settings.api_url}")
        
        # Package Builder initialisieren
        print("\n🏗️  Initialisiere Package Builder...")
        builder = CampaignPackageBuilder(
            prompts_dir=settings.get_prompts_dir_path(),
            questions_json_path=settings.get_questions_json_path()
        )
        print(f"   ✅ Prompts Dir: {settings.prompts_dir}")
        print(f"   ✅ Questions Path: {settings.questions_json_path}")
        
        # Package erstellen
        print("\n" + "="*70)
        package = builder.build_package(campaign_id, api)
        print("="*70)
        
        # Package speichern
        print("\n💾 Speichere Package...")
        path = storage.save_package(campaign_id, package)
        
        # Erfolgs-Ausgabe
        print("\n" + "="*70)
        print("✅ CAMPAIGN SETUP ABGESCHLOSSEN!")
        print("="*70)
        print(f"📦 Package: {path}")
        print(f"🏢 Company: {package['company_name']}")
        print(f"📋 Campaign: {package['campaign_name']}")
        print(f"❓ Fragen: {len(package['questions'].get('questions', []))}")
        print(f"📄 Templates: {len(package['kb_templates'])} Phasen")
        print("="*70)
        print("\n🔗 Bereit für Phase 2: Link-Generierung")
        print(f"   python generate_link.py --applicant-id <ID> --campaign-id {campaign_id}")
        print()
        
        sys.exit(0)
        
    except FileNotFoundError as e:
        print(f"\n❌ Fehler: {e}")
        sys.exit(1)
        
    except ValueError as e:
        print(f"\n❌ Validation Error: {e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def list_campaigns():
    """Listet alle gespeicherten Campaign Packages."""
    
    storage = CampaignStorage()
    campaigns = storage.list_campaigns()
    
    if not campaigns:
        print("\n📭 Keine Campaign Packages gefunden.")
        print("   Erstelle ein Package: python setup_campaign.py --campaign-id <ID>")
        return
    
    print("\n" + "="*70)
    print(f"📦 GESPEICHERTE CAMPAIGN PACKAGES ({len(campaigns)})")
    print("="*70 + "\n")
    
    for camp in campaigns:
        print(f"Campaign ID: {camp['campaign_id']}")
        print(f"  Company: {camp['company_name']}")
        print(f"  Campaign: {camp['campaign_name']}")
        print(f"  Erstellt: {camp['created_at']}")
        print(f"  Datei: {camp['file_path']}")
        print()


def main():
    """CLI Entry Point"""
    
    parser = argparse.ArgumentParser(
        description="Campaign Setup Tool - Erstellt KB Templates für Campaigns"
    )
    
    parser.add_argument(
        "--campaign-id",
        type=str,
        help="Campaign ID für Setup"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="Listet alle gespeicherten Campaigns"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Überschreibt existierendes Package"
    )
    
    args = parser.parse_args()
    
    # Liste oder Setup
    if args.list:
        list_campaigns()
    elif args.campaign_id:
        setup_campaign(args.campaign_id, args.force)
    else:
        parser.print_help()
        print("\n💡 Beispiele:")
        print("   python setup_campaign.py --campaign-id 16")
        print("   python setup_campaign.py --list")
        print("   python setup_campaign.py --campaign-id 16 --force")


if __name__ == "__main__":
    main()

