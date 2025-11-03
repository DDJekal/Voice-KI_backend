"""Test: ElevenLabs Conversational AI Conversations Methoden"""
import os
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")
agent_id = os.getenv("ELEVENLABS_AGENT_ID")

client = ElevenLabs(api_key=api_key)

print("="*70)
print("CONVERSATIONAL AI CONVERSATIONS METHODEN")
print("="*70)

# Prüfe conversations Methoden
print("client.conversational_ai.conversations Methoden:")
print([attr for attr in dir(client.conversational_ai.conversations) if not attr.startswith('_')])
print()

# Prüfe agents Methoden
print("client.conversational_ai.agents Methoden:")
print([attr for attr in dir(client.conversational_ai.agents) if not attr.startswith('_')])
print()

print("="*70)
print("HINWEIS:")
print("Falls 'create' oder 'start' dabei ist, funktioniert die API!")
print("="*70)

