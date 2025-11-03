"""Test: API Data Source"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_sources.api_loader import APIDataSource


def test_api_source():
    """Testet API Data Source mit echten Daten"""
    
    print("="*70)
    print("TEST: API DATA SOURCE")
    print("="*70)
    
    # HINWEIS: Bitte API_URL und API_KEY in .env setzen
    api_url = input("\nAPI URL eingeben (oder Enter für Production): ").strip()
    if not api_url:
        api_url = "https://high-office.hirings.cloud/api/v1"
    
    api_key = input("API KEY eingeben (oder Enter für leer): ").strip()
    
    status = input("Status (new/not_reached, oder Enter für 'new'): ").strip()
    if not status:
        status = "new"
    
    try:
        # Initialisiere API Source
        print(f"\n1. Verbinde zu API: {api_url}")
        print(f"   Status: {status}")
        print(f"   Test-Filter: Aktiv")
        
        api = APIDataSource(
            api_url=api_url,
            api_key=api_key if api_key else None,
            status=status,
            filter_test_applicants=True
        )
        
        print("\n2. Lade API-Daten...")
        applicants = api.list_pending_applicants()
        print(f"   ✅ {len(applicants)} Bewerber mit Status 'Neu intern' gefunden")
        
        if not applicants:
            print("\n⚠️  Keine Bewerber gefunden. Test beendet.")
            return
        
        # Teste mit erstem Bewerber
        first_applicant = applicants[0]
        print(f"\n3. Teste mit: {first_applicant['first_name']} {first_applicant['last_name']}")
        
        # Test Applicant Profile
        print("\n4. Lade Bewerberprofil...")
        profile = api.get_applicant_profile(first_applicant['telephone'])
        print(f"   ✅ Name: {profile['first_name']} {profile['last_name']}")
        print(f"   ✅ Telefon: {profile['telephone']}")
        print(f"   ✅ Campaign ID: {profile['campaign_id']}")
        
        # Test Address
        print("\n5. Lade Adresse...")
        address = api.get_applicant_address(first_applicant['telephone'])
        if address['street']:
            print(f"   ✅ Adresse: {address['street']} {address['house_number']}, {address['postal_code']} {address['city']}")
        else:
            print(f"   ℹ️  Adresse leer (wird im Gespräch erfragt)")
        
        # Test Company Profile
        print("\n6. Lade Unternehmensprofil...")
        campaign_id = str(first_applicant['campaign_id'])
        company = api.get_company_profile(campaign_id)
        print(f"   ✅ Unternehmen: {company['name']}")
        print(f"   ✅ Größe: {company['size']} Mitarbeitende")
        print(f"   ✅ Adresse: {company['address']}")
        print(f"   ✅ Benefits: {company['benefits'][:100]}..." if len(company['benefits']) > 100 else f"   ✅ Benefits: {company['benefits']}")
        
        # Test Conversation Protocol
        print("\n7. Lade Gesprächsprotokoll...")
        protocol = api.get_conversation_protocol(campaign_id)
        print(f"   ✅ Protokoll: {protocol['name']}")
        print(f"   ✅ Seiten: {len(protocol['pages'])}")
        
        if protocol['pages']:
            total_prompts = sum(len(page.get('prompts', [])) for page in protocol['pages'])
            print(f"   ✅ Gesamt Fragen: {total_prompts}")
        
        print("\n" + "="*70)
        print("✅ ALLE TESTS BESTANDEN!")
        print("="*70)
        print("\n💡 Nächster Schritt:")
        print("   Setze in .env: USE_API_SOURCE=true")
        print("   Dann kannst du main.py mit API-Daten nutzen")
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Tipp: Prüfe API_URL und API_KEY in .env")


if __name__ == "__main__":
    test_api_source()

