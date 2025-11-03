"""
Abstract Base Class für Call-Transport Layer.

Dieses Interface ermöglicht es, verschiedene Transport-Methoden
(WebRTC, Twilio, etc.) austauschbar zu nutzen.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ConversationTransport(ABC):
    """
    Abstract Base Class für Call-Transport.
    
    Implementierungen:
    - WebRTCConversation: Für lokale Audio I/O Tests
    - TwilioConversation: Für Telefon-Anrufe (später)
    """
    
    @abstractmethod
    def start_conversation(
        self,
        agent_id: str,
        knowledge_base: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Startet eine Voice Conversation.
        
        Args:
            agent_id: ElevenLabs Agent ID
            knowledge_base: Knowledge Base Text
            system_prompt: Optional system prompt override
            **kwargs: Transport-spezifische Parameter
            
        Returns:
            Dict mit conversation_id, status, etc.
        """
        pass
    
    @abstractmethod
    def end_conversation(self, conversation_id: str) -> None:
        """
        Beendet eine laufende Conversation.
        
        Args:
            conversation_id: ID der Conversation
        """
        pass
    
    @abstractmethod
    def get_conversation_status(self, conversation_id: str) -> Dict[str, Any]:
        """
        Holt Status einer Conversation.
        
        Args:
            conversation_id: ID der Conversation
            
        Returns:
            Dict mit Status-Informationen
        """
        pass

