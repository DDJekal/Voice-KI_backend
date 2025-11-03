"""Test: ElevenLabs SDK für Voice Agents"""
import os
from elevenlabs.client import ElevenLabs

# Lade Konfiguration
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")
agent_id = os.getenv("ELEVENLABS_AGENT_ID")

print("="*70)
print("ELEVENLABS SDK TEST")
print("="*70)
print(f"API Key: {api_key[:20]}...")
print(f"Agent ID: {agent_id}")
print()

# Erstelle Client
client = ElevenLabs(api_key=api_key)

print("Client erstellt erfolgreich!")
print()

# Versuche verfügbare Methoden zu inspizieren
print("Verfügbare Client-Attribute:")
print([attr for attr in dir(client) if not attr.startswith('_')])
print()

# Prüfe ob es ein "agents" oder "conversational_ai" Attribut gibt
if hasattr(client, 'agents'):
    print("client.agents gefunden!")
    print("Methoden:")
    print([attr for attr in dir(client.agents) if not attr.startswith('_')])
elif hasattr(client, 'conversational_ai'):
    print("client.conversational_ai gefunden!")
    print("Methoden:")
    print([attr for attr in dir(client.conversational_ai) if not attr.startswith('_')])
else:
    print("WARNUNG: Keine agents oder conversational_ai Methode gefunden!")
    print()
    print("Das bedeutet wahrscheinlich:")
    print("1. Voice Agents sind nicht über das Python SDK zugänglich")
    print("2. Du musst das ElevenLabs Dashboard für Agents nutzen")
    print("3. Oder es gibt eine WebSocket-basierte Integration")

