"""List all available campaigns from API"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.data_sources.api_loader import APIDataSource

def main():
    settings = get_settings()
    api = APIDataSource(
        api_url=settings.api_url,
        api_key=settings.api_key,
        status="new",
        filter_test_applicants=True
    )
    
    # Get all campaigns
    data = api._load_api_data()
    campaigns = data.get("campaigns", [])
    
    print(f"\nVerfuegbare Campaigns: {len(campaigns)}\n")
    print("="*70)
    
    for idx, c in enumerate(campaigns):
        campaign_id = c.get("id", idx)  # Nutze ID aus API oder Index als Fallback
        name = c.get("name", "Unnamed")
        
        print(f"Campaign ID: {campaign_id}")
        print(f"  Name: {name}")
        
        # Zeige ob es ein Gesprächsprotokoll gibt (heißt "transcript" in der API)
        protocol = c.get("transcript", {})
        if protocol and protocol.get("pages"):
            protocol_name = protocol.get("name", "Unknown")
            pages = len(protocol.get("pages", []))
            print(f"  Protocol: {protocol_name} ({pages} pages) *** HAS PROTOCOL ***")
        else:
            print(f"  Protocol: None")
        
        print()

if __name__ == "__main__":
    main()

