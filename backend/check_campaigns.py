"""
Check Available Campaigns in HOC API

Zeigt alle verfügbaren Campaign IDs und deren Namen.
"""

import requests
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

def check_campaigns():
    """Prüft verfügbare Campaigns in der API"""
    
    api_url = os.getenv('API_URL', 'https://high-office.hirings.cloud/api/v1')
    api_key = os.getenv('API_KEY')
    
    print("\n" + "="*70)
    print("🔍 Prüfe verfügbare Campaigns in HOC API")
    print("="*70)
    print(f"API URL: {api_url}")
    print(f"API Key: {api_key[:20]}..." if api_key else "❌ Kein API Key gesetzt")
    print("="*70 + "\n")
    
    if not api_key:
        print("❌ Fehler: API_KEY nicht in .env gesetzt!")
        print("   Setze in .env: API_KEY=dein-key-hier")
        sys.exit(1)
    
    try:
        # API-Call
        endpoint = f"{api_url}/applicants/new"
        print(f"📡 Rufe auf: {endpoint}")
        
        response = requests.get(
            endpoint,
            headers={'Authorization': f'{api_key}'},  # Kein "Bearer" Präfix!
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("\n❌ API-Key ist ungültig oder abgelaufen!")
            print("   Mögliche Ursachen:")
            print("   1. Key ist falsch")
            print("   2. Key ist abgelaufen")
            print("   3. Key hat keine Berechtigung für /applicants/new")
            print("\n💡 Prüfe den Key im HOC Dashboard")
            sys.exit(1)
        
        response.raise_for_status()
        data = response.json()
        
        # Zeige verfügbare Campaigns
        campaigns = data.get('campaigns', [])
        applicants = data.get('applicants', [])
        companies = data.get('companies', [])
        
        print(f"\n✅ API-Antwort erfolgreich geladen!")
        print(f"\n📊 Zusammenfassung:")
        print(f"   Bewerber: {len(applicants)}")
        print(f"   Companies: {len(companies)}")
        print(f"   Campaigns: {len(campaigns)}")
        
        if not campaigns:
            print("\n⚠️  Keine Campaigns gefunden!")
            print("   Die API-Antwort enthält keine 'campaigns' Liste.")
            print("\n   API-Response-Structure:")
            print(f"   Keys: {list(data.keys())}")
            
            # Zeige erste Applicant-Struktur
            if applicants and len(applicants) > 0:
                print("\n   Beispiel Applicant:")
                first_applicant = applicants[0]
                print(f"   - Applicant Keys: {list(first_applicant.keys())}")
                if 'campaign_id' in first_applicant:
                    print(f"   - Campaign ID: {first_applicant['campaign_id']}")
            
            sys.exit(0)
        
        print(f"\n📋 Verfügbare Campaigns:")
        print("-" * 70)
        
        for campaign in campaigns:
            campaign_id = campaign.get('id', 'N/A')
            campaign_name = campaign.get('name', 'Unbekannt')
            protocol = campaign.get('conversational_protocol', {})
            pages = protocol.get('pages', []) if protocol else []
            
            print(f"\n   Campaign ID: {campaign_id}")
            print(f"   Name: {campaign_name}")
            print(f"   Protocol-Pages: {len(pages)}")
            
            if pages:
                print(f"   Beispiel Page: {pages[0].get('name', 'N/A')}")
        
        print("\n" + "="*70)
        print("✅ Fertig! Nutze eine der Campaign IDs für Tests:")
        print(f"   python test_question_generator.py <CAMPAIGN_ID> --policy-level standard")
        print("="*70 + "\n")
        
    except requests.exceptions.Timeout:
        print("\n❌ Timeout: API antwortet nicht (>10s)")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request-Fehler: {e}")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_campaigns()

