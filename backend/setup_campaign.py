"""
Campaign Setup Tool - Phase 1 des 2-Phasen WebRTC Link Systems

Erstellt einmalig pro Campaign ein wiederverwendbares Package mit KB Templates.
Questions.json wird automatisch mit OpenAI generiert!
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.data_sources.api_loader import APIDataSource
from src.campaign.package_builder import CampaignPackageBuilder
from src.storage.campaign_storage import CampaignStorage


async def setup_campaign_async(
    campaign_id: str, 
    force: bool = False,
    enable_policies: bool = True,
    no_policies: bool = False,
    policy_level: str = "standard"
):
    """
    Erstellt Campaign Package und speichert lokal (async).
    
    Args:
        campaign_id: Campaign ID
        force: Überschreibt existierendes Package
        enable_policies: Enable conversation policies (default: True)
        no_policies: Disable policies (for A/B testing)
        policy_level: Policy level (basic, standard, advanced)
    """
    
    print("\n" + "="*70)
    print("🔧 CAMPAIGN SETUP - Phase 1 (mit automatischer Question Generation)")
    print("="*70)
    print(f"Campaign ID: {campaign_id}")
    
    # Policy-Config
    policies_enabled = enable_policies and not no_policies
    if policies_enabled:
        print(f"🔧 Policies: Aktiviert (Level: {policy_level})")
    else:
        print(f"ℹ️  Policies: Deaktiviert (A/B-Testing)")
    
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
        
        if not settings.openai_api_key:
            print("❌ Fehler: OPENAI_API_KEY nicht gesetzt!")
            print("   Benötigt für automatische Question Generation")
            sys.exit(1)
        
        api = APIDataSource(
            api_url=settings.api_url,
            api_key=settings.api_key,
            status="new",
            filter_test_applicants=True
        )
        print(f"   ✅ API URL: {settings.api_url}")
        
        # Package Builder initialisieren (ohne questions_json_path!)
        print("\n🏗️  Initialisiere Package Builder...")
        builder = CampaignPackageBuilder(
            prompts_dir=settings.get_prompts_dir_path(),
            policy_config={
                "enabled": policies_enabled,
                "level": policy_level
            }
        )
        print(f"   ✅ Prompts Dir: {settings.prompts_dir}")
        print(f"   ✅ Questions werden automatisch mit OpenAI generiert")
        print(f"   ✅ OpenAI Model: {settings.openai_model}")
        if policies_enabled:
            print(f"   ✅ Policies: {policy_level} level")
        
        # Package erstellen (jetzt async!)
        print("\n📦 Erstelle Campaign Package...")
        package = await builder.build_package(campaign_id, api)
        
        # Speichern
        print("\n💾 Speichere Package lokal...")
        storage.save_package(campaign_id, package)
        print(f"   ✅ Gespeichert: campaign_packages/{campaign_id}.json")
        
        print("\n" + "="*70)
        print("✅ CAMPAIGN SETUP ERFOLGREICH!")
        print("="*70)
        print(f"\n📦 Package Info:")
        print(f"   Company: {package['company_name']}")
        print(f"   Campaign: {package['campaign_name']}")
        print(f"   Fragen: {len(package['questions']['questions'])}")
        print(f"   Templates: {len(package['kb_templates'])} Phasen")
        print("\n" + "="*70 + "\n")
        
    except FileNotFoundError as e:
        print(f"\n❌ Fehler: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """CLI Entry Point"""
    parser = argparse.ArgumentParser(
        description="Campaign Setup Tool - Erstellt Campaign Packages mit automatischer Question Generation"
    )
    
    parser.add_argument(
        "--campaign-id",
        type=str,
        help="Campaign ID für Setup"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Überschreibt existierendes Package"
    )
    
    parser.add_argument(
        "--enable-policies",
        action="store_true",
        default=True,
        help="Enable conversation policies (default: enabled)"
    )
    
    parser.add_argument(
        "--no-policies",
        action="store_true",
        help="Disable policies (for A/B testing)"
    )
    
    parser.add_argument(
        "--policy-level",
        choices=["basic", "standard", "advanced"],
        default="standard",
        help="Policy level: basic (3 policies), standard (6 policies, default), advanced (7+ policies)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="Liste alle vorhandenen Packages"
    )
    
    args = parser.parse_args()
    
    if args.list:
        storage = CampaignStorage()
        packages = storage.list_packages()
        print("\n📦 Vorhandene Campaign Packages:")
        if not packages:
            print("   Keine Packages gefunden")
        else:
            for pkg_id in packages:
                print(f"   - {pkg_id}")
        print()
        sys.exit(0)
    
    if not args.campaign_id:
        parser.print_help()
        print("\n💡 Beispiele:")
        print("   python setup_campaign.py --campaign-id 16")
        print("   python setup_campaign.py --campaign-id 16 --force")
        print("   python setup_campaign.py --campaign-id 16 --policy-level advanced")
        print("   python setup_campaign.py --campaign-id 16 --no-policies  # A/B testing")
        print("   python setup_campaign.py --list")
        sys.exit(1)
    
    # Run async setup
    asyncio.run(setup_campaign_async(
        args.campaign_id, 
        args.force,
        args.enable_policies,
        args.no_policies,
        args.policy_level
    ))


if __name__ == "__main__":
    main()
