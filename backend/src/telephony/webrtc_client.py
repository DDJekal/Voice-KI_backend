"""
WebRTC Conversation Client - Für lokale Tests mit Audio I/O.

Nutzt ElevenLabs SDK für direkte Mikrofon/Lautsprecher Kommunikation.
Ideal für Tests und Agent-Entwicklung.
"""

import signal
import time
from typing import Dict, Any, Optional

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

from .base import ConversationTransport


class WebRTCConversation(ConversationTransport):
    """
    WebRTC-basierte Conversation für lokale Audio I/O.
    
    Verwendet:
    - Lokales Mikrofon für User-Input
    - Lokale Lautsprecher für Agent-Output
    
    Ideal für:
    - Entwicklung & Testing
    - Agent-Tuning
    - Proof of Concept
    
    NICHT für:
    - Automatisierte Telefon-Anrufe
    - Server-basierte Calls ohne Audio-Hardware
    """
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Initialisiert WebRTC Conversation Client.
        
        Args:
            api_key: ElevenLabs API Key
            base_url: Optional base URL (für EU/data residency)
                     EU: https://api.eu.residency.elevenlabs.io
        """
        self.api_key = api_key
        
        # Erstelle Client mit optionaler base_url
        if base_url:
            self.client = ElevenLabs(api_key=api_key, base_url=base_url)
            print(f"   ℹ️  Nutze Custom Base URL: {base_url}")
        else:
            self.client = ElevenLabs(api_key=api_key)
        
        self.active_conversations: Dict[str, Conversation] = {}
    
    def start_conversation(
        self,
        agent_id: str,
        knowledge_base: str,
        system_prompt: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Startet WebRTC Conversation mit Audio I/O.
        
        Args:
            agent_id: ElevenLabs Agent ID
            knowledge_base: Knowledge Base Text (wird NICHT überschrieben!)
            system_prompt: System Prompt (wird NICHT überschrieben!)
            user_id: Optional User ID für Tracking
            **kwargs: Weitere Parameter (werden ignoriert)
            
        Returns:
            Dict mit conversation_id, status, timestamp
            
        Note:
            ⚠️ WARNING: ElevenLabs SDK erlaubt KEIN Override von KB/System Prompt!
            Diese Parameter werden ignoriert. Agent-Konfiguration im Dashboard gilt.
            
            Für dynamische KB/Prompts: Später Twilio nutzen!
        """
        print(f"\n{'='*70}")
        print(f"🎙️  WebRTC Conversation wird gestartet...")
        print(f"{'='*70}")
        print(f"Agent ID: {agent_id}")
        print(f"User ID: {user_id or 'N/A'}")
        print(f"\n⚠️  HINWEIS:")
        print(f"   Knowledge Base ({len(knowledge_base)} Zeichen) wird IGNORIERT")
        print(f"   System Prompt wird IGNORIERT")
        print(f"   → Agent nutzt Dashboard-Konfiguration!")
        print(f"\n💡 Für dynamische KB: Später auf Twilio umsteigen")
        print(f"{'='*70}\n")
        
        # Erstelle Conversation
        conversation = Conversation(
            self.client,
            agent_id,
            
            # Auth nur wenn API Key gesetzt
            requires_auth=bool(self.api_key),
            
            # Standard Audio Interface (Mikrofon/Lautsprecher)
            audio_interface=DefaultAudioInterface(),
            
            # Callbacks für Logging
            callback_agent_response=lambda response: print(f"🤖 Agent: {response}"),
            callback_user_transcript=lambda transcript: print(f"👤 User: {transcript}"),
            callback_agent_response_correction=lambda orig, corr: print(f"🔄 Korrektur: {orig} → {corr}"),
        )
        
        # Starte Session
        print("▶️  Starte Session... (Sprechen Sie jetzt!)")
        
        # user_id Parameter nur übergeben wenn unterstützt
        try:
            conversation.start_session(user_id=user_id)
        except TypeError:
            # Fallback ohne user_id
            conversation.start_session()
        
        # Generiere temporäre Conversation ID
        conversation_id = f"webrtc_{int(time.time())}"
        self.active_conversations[conversation_id] = conversation
        
        # Signal Handler für sauberes Beenden (Ctrl+C)
        def cleanup(sig, frame):
            print(f"\n\n⏹️  Beende Conversation...")
            conversation.end_session()
        
        signal.signal(signal.SIGINT, cleanup)
        
        print(f"✅ Conversation gestartet!")
        print(f"   ID: {conversation_id}")
        print(f"   Drücken Sie Ctrl+C zum Beenden\n")
        
        return {
            "conversation_id": conversation_id,
            "status": "started",
            "agent_id": agent_id,
            "timestamp": time.time(),
            "transport": "webrtc",
            "warning": "KB/Prompt override not supported in WebRTC mode"
        }
    
    def wait_for_completion(self, conversation_id: str) -> str:
        """
        Wartet bis Conversation beendet ist.
        
        Args:
            conversation_id: ID der Conversation
            
        Returns:
            Finale Conversation ID von ElevenLabs
        """
        conversation = self.active_conversations.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} nicht gefunden")
        
        print(f"⏳ Warte auf Conversation-Ende...")
        final_id = conversation.wait_for_session_end()
        
        print(f"\n{'='*70}")
        print(f"✅ Conversation beendet!")
        print(f"   ElevenLabs Conversation ID: {final_id}")
        print(f"   Prüfen unter: https://elevenlabs.io/app/conversational-ai")
        print(f"{'='*70}\n")
        
        # Cleanup
        del self.active_conversations[conversation_id]
        
        return final_id
    
    def end_conversation(self, conversation_id: str) -> None:
        """
        Beendet eine laufende Conversation manuell.
        
        Args:
            conversation_id: ID der Conversation
        """
        conversation = self.active_conversations.get(conversation_id)
        if conversation:
            conversation.end_session()
            del self.active_conversations[conversation_id]
            print(f"⏹️  Conversation {conversation_id} beendet")
    
    def get_conversation_status(self, conversation_id: str) -> Dict[str, Any]:
        """
        Holt Status einer Conversation.
        
        Args:
            conversation_id: ID der Conversation
            
        Returns:
            Dict mit Status
        """
        is_active = conversation_id in self.active_conversations
        
        return {
            "conversation_id": conversation_id,
            "status": "active" if is_active else "ended",
            "transport": "webrtc"
        }

