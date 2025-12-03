"""Test Protocol Processor Endpoint"""

import json
import os
import sys

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system(f"{sys.executable} -m pip install requests")
    import requests

# Load test protocol
with open('test_protocol.json', 'r', encoding='utf-8') as f:
    protocol = json.load(f)

# API Configuration
API_URL = "https://voice-ki-backend.onrender.com/webhook/process-protocol"
WEBHOOK_SECRET = os.environ.get('VOICEKI_WEBHOOK_SECRET', 'test_secret')

print("=" * 70)
print("Testing Protocol Processor Endpoint")
print("=" * 70)
print(f"URL: {API_URL}")
print(f"Protocol ID: {protocol['id']}")
print(f"Protocol Name: {protocol['name']}")
print(f"Pages: {len(protocol['pages'])}")
print("=" * 70)

try:
    response = requests.post(
        API_URL,
        headers={
            'Authorization': f'Bearer {WEBHOOK_SECRET}',
            'Content-Type': 'application/json'
        },
        json=protocol,
        timeout=60
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ SUCCESS!")
        print("=" * 70)
        print(f"Protocol ID: {result['protocol_id']}")
        print(f"Protocol Name: {result['protocol_name']}")
        print(f"Processed At: {result['processed_at']}")
        print(f"Question Count: {result['question_count']}")
        print("=" * 70)
        
        if result['questions']:
            print("\nFirst 3 Generated Questions:")
            print("-" * 70)
            for i, q in enumerate(result['questions'][:3], 1):
                print(f"\n{i}. {q['id']}")
                print(f"   Question: {q['question']}")
                print(f"   Type: {q['type']}")
                print(f"   Priority: {q['priority']}")
                print(f"   Group: {q.get('group', 'N/A')}")
        
        # Save result
        with open('test_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 70)
        print("✅ Full result saved to: test_result.json")
        print("=" * 70)
        
    else:
        print(f"\n❌ ERROR {response.status_code}")
        print("=" * 70)
        print("Response:")
        print(response.text)
        print("=" * 70)

except requests.exceptions.Timeout:
    print("\n⏱️ TIMEOUT - Request took longer than 60 seconds")
    print("This might mean OpenAI is processing the protocol (can take 30-60s)")
    print("Try again in a moment!")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

