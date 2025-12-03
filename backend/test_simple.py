"""Simple Test ohne Unicode"""
import json
import requests

with open('test_protocol.json', 'r', encoding='utf-8') as f:
    protocol = json.load(f)

response = requests.post(
    "https://voice-ki-backend.onrender.com/webhook/process-protocol",
    headers={
        'Authorization': 'Bearer 8f15988e07ad5bef0a7050e91b7f3ebe',
        'Content-Type': 'application/json'
    },
    json=protocol,
    timeout=120
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    
    with open('test_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"SUCCESS! Generated {result['question_count']} questions")
    print(f"Saved to: test_result.json")
else:
    print(f"ERROR: {response.text}")

