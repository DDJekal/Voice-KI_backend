"""Debug: ElevenLabs API Endpoint Tester"""
import requests
import json

api_key = input("ElevenLabs API Key: ").strip()
agent_id = input("Agent ID: ").strip()

# Teste verschiedene Endpoints
endpoints = [
    "https://api.elevenlabs.io/v1/convai/conversations",
    "https://api.elevenlabs.io/v1/conversational-ai/conversations",
    "https://api.elevenlabs.io/v1/conversational-ai/conversation",
    "https://api.elevenlabs.io/v1/agents/{agent_id}/conversations",
    "https://api.elevenlabs.io/v1/agents/{agent_id}/conversation",
]

headers = {
    "xi-api-key": api_key,
    "Content-Type": "application/json"
}

payload = {
    "agent_id": agent_id,
    "override_agent_config": {
        "prompt": {
            "knowledge_base": "Test Knowledge Base",
            "system": "Test System Prompt"
        }
    }
}

print("\n" + "="*70)
print("TESTE VERSCHIEDENE ENDPOINTS")
print("="*70 + "\n")

for endpoint_template in endpoints:
    endpoint = endpoint_template.replace("{agent_id}", agent_id)
    print(f"Teste: {endpoint}")
    
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"  SUCCESS! Korrekter Endpoint gefunden!")
            print(f"  Volle Response:")
            print(json.dumps(response.json(), indent=2))
            break
            
    except Exception as e:
        print(f"  Error: {str(e)}")
    
    print()

print("\n" + "="*70)
print("HINWEIS: Falls alle fehlschlagen, ist WebSocket moeglicherweise noetig")
print("="*70)

