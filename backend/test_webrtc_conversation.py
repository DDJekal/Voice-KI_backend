"""
Test: WebRTC Conversation mit ElevenLabs Agent.

Dieser Test startet eine lokale Audio-Conversation:
- Mikrofon → User Input
- Lautsprecher → Agent Output

WICHTIG:
- Agent nutzt Dashboard-Konfiguration (KB/Prompts)
- Dynamische KB/Prompts werden IGNORIERT
- Nur für Tests & Agent-Entwicklung
"""

import sys
import os

# Safe stdout für Unicode
class SafeStdout:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
    def write(self, text):
        try:
            self.original_stdout.write(text)
        except UnicodeEncodeError:
            text_clean = text.encode('ascii', errors='ignore').decode('ascii')
            self.original_stdout.write(text_clean)
    def flush(self):
        self.original_stdout.flush()

sys.stdout = SafeStdout(sys.stdout)

from dotenv import load_dotenv
load_dotenv()

from src.telephony.webrtc_client import WebRTCConversation
from src.data_sources.file_loader import FileDataSource
from src.aggregator.knowledge_base_builder import KnowledgeBaseBuilder
from src.config import get_settings


def main():
    print("="*70)
    print("VOICEKI - WEBRTC CONVERSATION TEST")
    print("="*70)
    print()
    print("Dieser Test startet eine lokale Audio-Conversation.")
    print("Sie koennen direkt mit dem Agent sprechen!")
    print()
    print("WICHTIG:")
    print("  - Mikrofon wird verwendet (User Input)")
    print("  - Lautsprecher werden verwendet (Agent Output)")
    print("  - Agent nutzt Dashboard-Konfiguration")
    print("  - Dynamische KB/Prompts werden IGNORIERT")
    print()
    print("Druecken Sie Ctrl+C zum Beenden")
    print("="*70)
    print()
    
    # Konfiguration
    settings = get_settings()
    api_key = settings.elevenlabs_api_key
    agent_id = settings.elevenlabs_agent_id
    
    if not api_key or not agent_id:
        print("FEHLER: ELEVENLABS_API_KEY oder ELEVENLABS_AGENT_ID nicht gesetzt!")
        print("Bitte .env Datei pruefen.")
        sys.exit(1)
    
    print(f"Agent ID: {agent_id}")
    print()
    
    # EU Data Residency - korrekte URL verwenden
    base_url = "https://api.eu.residency.elevenlabs.io"
    print("ℹ️  EU Data Residency aktiviert")
    print(f"   API Endpoint: {base_url}")
    print()
    
    # Lade Daten (nur für Demo - werden ignoriert!)
    print("Lade Beispiel-Daten (werden NICHT verwendet)...")
    data_source = FileDataSource(settings.get_data_dir_path())
    
    try:
        applicant = data_source.get_applicant_profile("test")
        company = data_source.get_company_profile("test")
        
        # Baue Knowledge Base (wird ignoriert!)
        kb_builder = KnowledgeBaseBuilder(settings.get_prompts_dir_path())
        
        phase_data = {
            "candidatefirst_name": applicant.get("first_name", "Max"),
            "candidatelast_name": applicant.get("last_name", "Mustermann"),
        }
        
        kb = kb_builder.build_phase_1(phase_data)
        
        print(f"  Knowledge Base erstellt: {len(kb)} Zeichen")
        print(f"  (Diese wird vom Agent IGNORIERT!)")
        print()
        
    except Exception as e:
        print(f"  Warnung: Konnte Daten nicht laden: {e}")
        print(f"  Fahre ohne Daten fort...")
        kb = "Test Knowledge Base"
    
    # Erstelle WebRTC Client
    client = WebRTCConversation(api_key=api_key, base_url=base_url)
    
    # Starte Conversation
    result = client.start_conversation(
        agent_id=agent_id,
        knowledge_base=kb,  # Wird ignoriert!
        system_prompt="Test System Prompt",  # Wird ignoriert!
        user_id="test_user"
    )
    
    print(f"\nConversation ID: {result['conversation_id']}")
    print(f"Status: {result['status']}")
    print()
    
    # Warte auf Completion
    try:
        final_id = client.wait_for_completion(result['conversation_id'])
        print(f"\nFINALE ELEVENLABS ID: {final_id}")
        
    except KeyboardInterrupt:
        print("\n\nBeende Conversation...")
        client.end_conversation(result['conversation_id'])
        print("Conversation beendet.")


if __name__ == "__main__":
    main()

