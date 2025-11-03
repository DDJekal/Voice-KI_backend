"""
Mock Transport Client - Für Tests ohne echte API Calls.

Simuliert einen Call ohne tatsächliche Netzwerk-Verbindung.
"""

import time
from typing import Dict, Any, Optional

from .base import ConversationTransport


class MockConversationClient(ConversationTransport):
    """
    Mock Transport für Tests.
    
    Simuliert Conversations ohne echte API Calls.
    Ideal für Dry-Runs und Unit Tests.
    """
    
    def __init__(self):
        """Initialisiert Mock Client"""
        self.conversations = {}
    
    def start_conversation(
        self,
        agent_id: str,
        knowledge_base: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Simuliert Conversation Start.
        
        Args:
            agent_id: Agent ID
            knowledge_base: Knowledge Base
            system_prompt: System Prompt
            **kwargs: Weitere Parameter
            
        Returns:
            Dict mit mock conversation_id
        """
        conversation_id = f"mock_conv_{int(time.time())}"
        
        self.conversations[conversation_id] = {
            "agent_id": agent_id,
            "kb_size": len(knowledge_base),
            "has_system_prompt": system_prompt is not None,
            "started_at": time.time()
        }
        
        print(f"\n[MOCK] ElevenLabs Conversation gestartet:")
        print(f"  Conversation ID: {conversation_id}")
        print(f"  Agent ID: {agent_id}")
        print(f"  Knowledge Base: {len(knowledge_base)} Zeichen")
        if system_prompt:
            print(f"  System Prompt: {len(system_prompt)} Zeichen")
        
        return {
            "conversation_id": conversation_id,
            "status": "started",
            "agent_id": agent_id,
            "timestamp": time.time(),
            "transport": "mock"
        }
    
    def end_conversation(self, conversation_id: str) -> None:
        """Beendet Mock Conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            print(f"[MOCK] Conversation {conversation_id} beendet")
    
    def get_conversation_status(self, conversation_id: str) -> Dict[str, Any]:
        """Holt Mock Conversation Status"""
        if conversation_id in self.conversations:
            return {
                "conversation_id": conversation_id,
                "status": "active",
                "transport": "mock",
                **self.conversations[conversation_id]
            }
        return {
            "conversation_id": conversation_id,
            "status": "not_found",
            "transport": "mock"
        }

