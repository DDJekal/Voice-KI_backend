"""Test: Erster echter ElevenLabs Call"""
import sys

# Patch stdout für Unicode
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

from src.data_sources.file_loader import FileDataSource
from src.elevenlabs.voice_client import ElevenLabsVoiceClient
from src.orchestrator.call_orchestrator import CallOrchestrator
from src.config import get_settings

def main():
    settings = get_settings()
    settings.dry_run = False
    
    print("="*70)
    print("WARNUNG: Echter ElevenLabs Call!")
    print("Kosten: ca. 0.10 EUR pro Minute")
    print("="*70)
    
    confirm = input("\nFortfahren? (ja/nein): ")
    if confirm.lower() != 'ja':
        print("Abgebrochen.")
        return
    
    data_source = FileDataSource(settings.data_dir)
    elevenlabs_client = ElevenLabsVoiceClient(settings.elevenlabs_api_key)
    orchestrator = CallOrchestrator(data_source, elevenlabs_client, settings)
    
    result = orchestrator.start_call("test", "test")
    
    print(f"\nCall gestartet!")
    print(f"Conversation ID: {result['conversation_id']}")
    print(f"\nPruefen unter:")
    print(f"https://elevenlabs.io/app/conversational-ai")

if __name__ == "__main__":
    main()

