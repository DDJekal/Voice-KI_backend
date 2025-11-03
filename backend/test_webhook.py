"""
Test Webhook locally

Tests den FastAPI Webhook-Endpoint gegen einen lokal laufenden Server.
"""

import requests
import json
import sys


def test_webhook_local(campaign_id: str = "16", force: bool = False):
    """
    Testet Webhook gegen lokalen Server.
    
    Args:
        campaign_id: Campaign ID zum Testen
        force: Force rebuild Flag
    """
    
    url = "http://localhost:8000/webhook/setup-campaign"
    
    payload = {
        "campaign_id": campaign_id,
        "force_rebuild": force
    }
    
    headers = {
        "Authorization": "Bearer test_secret",
        "Content-Type": "application/json"
    }
    
    print("="*70)
    print("TEST: Webhook Setup Campaign")
    print("="*70)
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("="*70 + "\n")
    
    try:
        print("📤 Sende Request...")
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        print(f"\n📨 Response:")
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"\n📦 Package Info:")
            print(f"   Package ID: {result.get('package_id')}")
            print(f"   Company: {result.get('company_name')}")
            print(f"   Created: {result.get('created_at')}")
            print(f"   Questions: {result.get('question_count')}")
            print(f"   Download URL: {result.get('download_url')}")
            print(f"\n{json.dumps(result, indent=2)}")
        else:
            print(f"\n❌ ERROR!")
            print(f"\n{response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Fehler: Server nicht erreichbar!")
        print("   Starte Server mit: uvicorn api_server:app --reload")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("\n❌ Fehler: Request Timeout (>60s)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_health_check():
    """Testet Health Check Endpoint"""
    url = "http://localhost:8000/health"
    
    print("\n" + "="*70)
    print("TEST: Health Check")
    print("="*70)
    
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Server is healthy!")
            print(f"   Status: {result.get('status')}")
            print(f"   Version: {result.get('version')}")
            print(f"   Timestamp: {result.get('timestamp')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Server nicht erreichbar!")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Webhook lokal")
    parser.add_argument("--campaign-id", default="16", help="Campaign ID")
    parser.add_argument("--force", action="store_true", help="Force rebuild")
    parser.add_argument("--health-only", action="store_true", help="Nur Health Check")
    
    args = parser.parse_args()
    
    if args.health_only:
        test_health_check()
    else:
        test_health_check()
        test_webhook_local(args.campaign_id, args.force)

