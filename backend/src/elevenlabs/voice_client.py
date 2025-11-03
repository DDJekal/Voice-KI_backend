"""ElevenLabs Voice Client - API Integration für Conversational AI"""

import requests
import time
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ElevenLabsVoiceClient:
    """
    Client für ElevenLabs Conversational AI API.
    Startet und verwaltet Voice Conversations.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.elevenlabs.io/v1"):
        """
        Initialisiert ElevenLabs Client.
        
        Args:
            api_key: ElevenLabs API Key
            base_url: Base URL der API (default: production)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Erstellt Session mit Retry-Logik"""
        session = requests.Session()
        
        # Retry Strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session

    def start_conversation(
        self, 
        agent_id: str, 
        knowledge_base: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Startet eine neue Voice Conversation mit ElevenLabs.
        
        Args:
            agent_id: ElevenLabs Agent ID
            knowledge_base: Knowledge Base Text für den Agent
            system_prompt: Optional system prompt override
            
        Returns:
            Dict mit conversation_id und Status
            
        Raises:
            requests.HTTPError: Bei API-Fehlern
        """
        # Korrigierter Endpoint (ohne /v1 prefix, da bereits in base_url)
        endpoint = f"{self.base_url}/conversational-ai/conversations"
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "agent_id": agent_id,
            "override_agent_config": {
                "prompt": {
                    "knowledge_base": knowledge_base
                }
            }
        }
        
        # Optional: System Prompt überschreiben
        if system_prompt:
            payload["override_agent_config"]["prompt"]["system"] = system_prompt
        
        try:
            response = self.session.post(
                endpoint, 
                headers=headers, 
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "conversation_id": data.get("conversation_id"),
                "status": "started",
                "agent_id": agent_id,
                "timestamp": time.time()
            }
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"ElevenLabs API Error: {str(e)}")

    def get_conversation_status(self, conversation_id: str) -> Dict[str, Any]:
        """
        Holt Status einer laufenden Conversation.
        
        Args:
            conversation_id: ID der Conversation
            
        Returns:
            Dict mit Status-Informationen
        """
        endpoint = f"{self.base_url}/convai/conversations/{conversation_id}"
        
        headers = {
            "xi-api-key": self.api_key
        }
        
        try:
            response = self.session.get(
                endpoint, 
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get conversation status: {str(e)}")

    def get_transcript(self, conversation_id: str) -> Optional[str]:
        """
        Holt Transkript einer beendeten Conversation.
        
        Args:
            conversation_id: ID der Conversation
            
        Returns:
            Transkript-Text oder None
        """
        endpoint = f"{self.base_url}/convai/conversations/{conversation_id}/transcript"
        
        headers = {
            "xi-api-key": self.api_key
        }
        
        try:
            response = self.session.get(
                endpoint, 
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("transcript")
            
        except requests.exceptions.RequestException as e:
            print(f"Warning: Could not fetch transcript: {str(e)}")
            return None

    def wait_for_completion(
        self, 
        conversation_id: str, 
        timeout: int = 3600,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Wartet auf Completion einer Conversation (blocking).
        
        Args:
            conversation_id: ID der Conversation
            timeout: Max. Wartezeit in Sekunden
            poll_interval: Polling-Intervall in Sekunden
            
        Returns:
            Final status dict
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_conversation_status(conversation_id)
            
            # Check if completed
            if status.get("status") in ["completed", "ended", "failed"]:
                return status
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Conversation did not complete within {timeout}s")


class MockElevenLabsClient(ElevenLabsVoiceClient):
    """
    Mock-Client für Tests ohne echte API-Calls.
    Simuliert ElevenLabs-Verhalten.
    """

    def __init__(self):
        """Initialisiert Mock-Client ohne API Key"""
        self.api_key = "mock_key"
        self.base_url = "mock://elevenlabs"
        self.conversations = {}

    def start_conversation(
        self, 
        agent_id: str, 
        knowledge_base: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Simuliert Conversation-Start"""
        conversation_id = f"mock_conv_{int(time.time())}"
        
        self.conversations[conversation_id] = {
            "agent_id": agent_id,
            "knowledge_base": knowledge_base[:100] + "...",
            "status": "started",
            "transcript": None
        }
        
        print(f"\n[MOCK] ElevenLabs Conversation gestartet:")
        print(f"  Conversation ID: {conversation_id}")
        print(f"  Agent ID: {agent_id}")
        print(f"  Knowledge Base: {len(knowledge_base)} Zeichen")
        
        return {
            "conversation_id": conversation_id,
            "status": "started",
            "agent_id": agent_id,
            "timestamp": time.time()
        }

    def get_conversation_status(self, conversation_id: str) -> Dict[str, Any]:
        """Simuliert Status-Abfrage"""
        if conversation_id not in self.conversations:
            raise Exception(f"Conversation not found: {conversation_id}")
        
        return {
            "conversation_id": conversation_id,
            "status": "completed",
            **self.conversations[conversation_id]
        }

    def get_transcript(self, conversation_id: str) -> Optional[str]:
        """Simuliert Transkript-Abfrage"""
        return "[MOCK] Transkript würde hier stehen..."

    def wait_for_completion(self, conversation_id: str, timeout: int = 3600, poll_interval: int = 5) -> Dict[str, Any]:
        """Simuliert sofortige Completion"""
        return self.get_conversation_status(conversation_id)

