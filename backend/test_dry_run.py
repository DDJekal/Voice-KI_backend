"""Test: Dry-Run ohne Emojis"""
import sys
import os
import io

# Setze UTF-8 Encoding und patche stdout
class SafeStdout:
    """Wrapper für stdout, der Unicode-Fehler abfängt"""
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        
    def write(self, text):
        try:
            self.original_stdout.write(text)
        except UnicodeEncodeError:
            # Fallback: Entferne nicht-ASCII Zeichen
            text_clean = text.encode('ascii', errors='ignore').decode('ascii')
            self.original_stdout.write(text_clean)
    
    def flush(self):
        self.original_stdout.flush()

# Patche stdout
sys.stdout = SafeStdout(sys.stdout)

from src.data_sources.file_loader import FileDataSource
from src.telephony.mock_client import MockConversationClient
from src.orchestrator.call_orchestrator import CallOrchestrator
from src.config import get_settings

def main():
    print("="*70)
    print("VOICEKI BACKEND - DRY-RUN TEST")
    print("="*70)
    
    # Settings
    settings = get_settings()
    settings.dry_run = True
    
    print(f"Modus: DRY-RUN (Mock)")
    print(f"Data Dir: {settings.data_dir}")
    print("="*70)
    print()
    
    try:
        # Data Source
        data_source = FileDataSource(settings.data_dir)
        
        # Mock Client
        print("Verwende Mock-Client (kein echter API Call)")
        conversation_client = MockConversationClient()
        
        # Orchestrator
        orchestrator = CallOrchestrator(
            data_source=data_source,
            conversation_client=conversation_client,
            settings=settings
        )
        
        # Start Call
        print()
        result = orchestrator.start_call(
            applicant_id="test",
            campaign_id="test"
        )
        
        # Ergebnis
        print()
        print("="*70)
        print("ERGEBNIS")
        print("="*70)
        print(f"Conversation ID: {result.get('conversation_id')}")
        print(f"Status: {result.get('status')}")
        if 'phases' in result:
            print(f"Phasen: {result['phases']}")
        if 'knowledge_base_size' in result:
            print(f"Knowledge Base: {result['knowledge_base_size']} Zeichen")
        print("="*70)
        print()
        print("OK - Dry-Run erfolgreich!")
        
    except Exception as e:
        print()
        print("="*70)
        print("FEHLER")
        print("="*70)
        print(f"{type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

