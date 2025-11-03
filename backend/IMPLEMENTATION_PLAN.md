# 📋 Umsetzungsplan: VoiceKI ElevenLabs Integration

**Ziel:** Vollständige Integration der ElevenLabs Conversational AI mit dynamischen Prompts und Knowledge Bases

**Status:** API getestet ✅ | Bereit für Implementation

---

## Phase 1: Master Prompt & Phase-Prompts Integration

**Priorität:** 🔴 KRITISCH  
**Zeit:** ~1-2 Stunden  
**Abhängigkeiten:** Keine

### 1.1 Master Prompt als System Prompt übergeben

**Dateien:** 
- `backend/src/orchestrator/call_orchestrator.py`
- `VoiceKI _prompts/Masterprompt.md`

**Änderungen:**

```python
# In call_orchestrator.py

def _load_master_prompt(self) -> str:
    """Lädt Master Prompt aus Markdown-Datei"""
    prompt_file = self.settings.get_prompts_dir_path() / "Masterprompt.md"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Master Prompt nicht gefunden: {prompt_file}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()

def start_call(self, applicant_id, campaign_id, phase=None):
    # ... existing code ...
    
    # NEU: Lade Master Prompt
    master_prompt = self._load_master_prompt()
    
    # NEU: Übergebe an ElevenLabs
    result = self.elevenlabs_client.start_conversation(
        agent_id=self.settings.elevenlabs_agent_id,
        knowledge_base=combined_kb,
        system_prompt=master_prompt  # ← NEU!
    )
```

**Test:**
```bash
cd backend
venv\Scripts\python.exe test_dry_run.py
```

**Erwartetes Ergebnis:**
- Master Prompt wird geladen
- Keine Fehler
- Mock-Call funktioniert

---

### 1.2 Phase-Prompts in Knowledge Bases integrieren

**Dateien:**
- `backend/src/aggregator/knowledge_base_builder.py`
- `VoiceKI _prompts/Phase_1.md`, `Phase_2.md`, `Phase_3.md`, `Phase_4.md`

**Änderungen:**

```python
# In knowledge_base_builder.py

class KnowledgeBaseBuilder:
    def __init__(self, prompts_dir: Path = None):
        """
        Args:
            prompts_dir: Pfad zu VoiceKI _prompts/ Ordner
        """
        if prompts_dir is None:
            prompts_dir = Path("../VoiceKI _prompts")
        self.prompts_dir = prompts_dir
    
    def _load_phase_prompt(self, phase_number: int) -> str:
        """Lädt Phase-Prompt aus Markdown-Datei"""
        prompt_file = self.prompts_dir / f"Phase_{phase_number}.md"
        
        if not prompt_file.exists():
            return f"# Phase {phase_number}\n(Prompt-Datei nicht gefunden)"
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def build_phase_1(self, data: Dict[str, Any]) -> str:
        # Lade Phase-Prompt
        phase_prompt = self._load_phase_prompt(1)
        
        kb = f"""{'='*80}
PHASE 1: BEGRÜSSUNG & KONTAKTDATEN
{'='*80}

{phase_prompt}

{'='*80}
DATEN FÜR DIESE PHASE
{'='*80}

Name: {data.get('candidatefirst_name')} {data.get('candidatelast_name')}
Rolle: {data.get('campaignrole_title')}
Standort: {data.get('campaignlocation_label')}
...
"""
        return kb
    
    # Analog für build_phase_2, build_phase_3, build_phase_4
```

**In call_orchestrator.py:**

```python
def __init__(self, data_source, elevenlabs_client, settings):
    # ...
    self.kb_builder = KnowledgeBaseBuilder(
        prompts_dir=settings.get_prompts_dir_path()  # ← NEU: Pfad übergeben
    )
```

**Test:**
```bash
venv\Scripts\python.exe test_dry_run.py
```

**Erwartetes Ergebnis:**
- Knowledge Bases sind größer (>15.000 Zeichen statt 10.000)
- Phase-Prompts sind in `Output_ordner/knowledge_base_phase*.txt` sichtbar

---

### 1.3 Validierung mit echtem ElevenLabs Call

**Vorsichtsmaßnahme:** Erst mit minimaler Knowledge Base testen!

**Test-Script erstellen:** `backend/test_real_call.py`

```python
"""Test: Erster echter ElevenLabs Call"""
from src.data_sources.file_loader import FileDataSource
from src.elevenlabs.voice_client import ElevenLabsVoiceClient
from src.orchestrator.call_orchestrator import CallOrchestrator
from src.config import get_settings

def main():
    settings = get_settings()
    settings.dry_run = False  # ← ECHT!
    
    print("="*70)
    print("WARNUNG: Echter ElevenLabs Call wird gestartet!")
    print("Kosten: ca. 0.10 EUR")
    print("="*70)
    
    confirm = input("Fortfahren? (ja/nein): ")
    if confirm.lower() != 'ja':
        print("Abgebrochen.")
        return
    
    data_source = FileDataSource(settings.data_dir)
    elevenlabs_client = ElevenLabsVoiceClient(
        api_key=settings.elevenlabs_api_key
    )
    orchestrator = CallOrchestrator(data_source, elevenlabs_client, settings)
    
    result = orchestrator.start_call("test", "test")
    
    print(f"\n✅ Call gestartet!")
    print(f"Conversation ID: {result['conversation_id']}")
    print(f"\nGehe zu: https://elevenlabs.io/app/conversational-ai")
    print(f"Finde Conversation: {result['conversation_id']}")

if __name__ == "__main__":
    main()
```

**Ausführen:**
```bash
venv\Scripts\python.exe test_real_call.py
```

**Prüfen:**
1. ElevenLabs Dashboard öffnen
2. Conversation finden
3. Aufnahme anhören
4. Transkript prüfen
5. Prompts prüfen (im Debug-Modus sichtbar)

---

## Phase 2: Output & Logging

**Priorität:** 🟡 WICHTIG  
**Zeit:** ~1 Stunde  
**Abhängigkeiten:** Phase 1 abgeschlossen

### 2.1 Transkript-Abruf implementieren

**Dateien:**
- `backend/src/orchestrator/call_orchestrator.py`
- `backend/src/config.py`

**Änderungen in config.py:**

```python
class Settings(BaseSettings):
    # ...
    
    # Call Management
    wait_for_completion: bool = Field(
        default=False,
        description="Warten bis Call abgeschlossen ist und Transkript abrufen"
    )
    completion_timeout: int = Field(
        default=1800,
        description="Max. Wartezeit für Call-Completion in Sekunden (30 Min)"
    )
```

**Änderungen in call_orchestrator.py:**

```python
def start_call(self, applicant_id, campaign_id, phase=None):
    # ... existing code ...
    
    result = self._start_multi_phase_call(knowledge_bases)
    
    # NEU: Optional warten & Transkript abrufen
    if self.settings.wait_for_completion:
        safe_print("\n⏳ Warte auf Call-Abschluss...")
        final_status = self.elevenlabs_client.wait_for_completion(
            conversation_id=result['conversation_id'],
            timeout=self.settings.completion_timeout
        )
        
        # Hole Transkript
        safe_print("📄 Lade Transkript...")
        transcript = self.elevenlabs_client.get_transcript(
            result['conversation_id']
        )
        
        # Speichere
        self._save_call_results(
            conversation_id=result['conversation_id'],
            applicant_id=applicant_id,
            knowledge_base=combined_kb,
            transcript=transcript
        )
        
        result['transcript'] = transcript
    
    return result
```

---

### 2.2 Strukturierte Output-Speicherung

**Neue Dateien:**
- `backend/Output_ordner/calls/{conversation_id}_metadata.json`
- `backend/Output_ordner/calls/{conversation_id}_transcript.txt`
- `backend/Output_ordner/calls/{conversation_id}_knowledge_base.txt`

**Implementierung in call_orchestrator.py:**

```python
def _save_call_results(
    self,
    conversation_id: str,
    applicant_id: str,
    knowledge_base: str,
    transcript: Optional[str] = None
):
    """Speichert Call-Ergebnisse persistent"""
    from datetime import datetime
    import json
    
    output_dir = Path("Output_ordner/calls")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Metadata
    metadata = {
        "conversation_id": conversation_id,
        "applicant_id": applicant_id,
        "timestamp": datetime.now().isoformat(),
        "kb_size": len(knowledge_base),
        "has_transcript": transcript is not None
    }
    
    with open(output_dir / f"{conversation_id}_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Knowledge Base
    with open(output_dir / f"{conversation_id}_kb.txt", "w", encoding="utf-8") as f:
        f.write(knowledge_base)
    
    # Transkript
    if transcript:
        with open(output_dir / f"{conversation_id}_transcript.txt", "w", encoding="utf-8") as f:
            f.write(transcript)
    
    safe_print(f"   ✓ Ergebnisse gespeichert: Output_ordner/calls/{conversation_id}_*")
```

**Test:**
```bash
# Mit wait_for_completion=True in .env
venv\Scripts\python.exe test_real_call.py
```

---

### 2.3 Logging einrichten

**Neue Datei:** `backend/src/utils/logger.py`

```python
"""Logging Utility für VoiceKI Backend"""
import logging
from pathlib import Path
from datetime import datetime

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Erstellt Logger mit Console und File Handler.
    
    Args:
        name: Logger Name
        level: Log Level (default: INFO)
        
    Returns:
        Konfigurierter Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Verhindere doppelte Handler
    if logger.handlers:
        return logger
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File Handler
    log_dir = Path("Output_ordner/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"{name}_{timestamp}.log"
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
```

**Integration in call_orchestrator.py:**

```python
from ..utils.logger import setup_logger

class CallOrchestrator:
    def __init__(self, data_source, elevenlabs_client, settings):
        # ...
        self.logger = setup_logger("call_orchestrator")
    
    def start_call(self, applicant_id, campaign_id, phase=None):
        self.logger.info(f"Starting call - Applicant: {applicant_id}, Campaign: {campaign_id}")
        
        try:
            # ... existing code ...
            self.logger.info(f"Call started successfully - Conv ID: {result['conversation_id']}")
            return result
        except Exception as e:
            self.logger.error(f"Call failed: {str(e)}", exc_info=True)
            raise
```

---

## Phase 3: Production Features (Optional)

**Priorität:** 🟢 NICE-TO-HAVE  
**Zeit:** ~2-3 Stunden  
**Abhängigkeiten:** Phase 1 & 2 abgeschlossen

### 3.1 Webhook für Call-Completion

**Neue Datei:** `backend/webhook_server.py`

```python
"""FastAPI Webhook Server für ElevenLabs Completion Events"""
from fastapi import FastAPI, Request
from src.elevenlabs.voice_client import ElevenLabsVoiceClient
from src.config import get_settings
import json

app = FastAPI()
settings = get_settings()
client = ElevenLabsVoiceClient(settings.elevenlabs_api_key)

@app.post("/elevenlabs/completion")
async def handle_completion(request: Request):
    """Webhook Endpoint für Call-Completion Events"""
    data = await request.json()
    
    conversation_id = data.get("conversation_id")
    status = data.get("status")
    
    if status == "completed":
        # Hole Transkript
        transcript = client.get_transcript(conversation_id)
        
        # Speichere
        output_file = f"Output_ordner/calls/{conversation_id}_transcript.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(transcript)
        
        return {"status": "success", "saved": output_file}
    
    return {"status": "ignored"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**ElevenLabs Konfiguration:**
- Webhook URL: `https://your-domain.com/elevenlabs/completion`
- Events: `conversation.completed`

---

### 3.2 Error Handling & Retries

**Implementierung in call_orchestrator.py:**

```python
import time

def start_call_with_retry(
    self, 
    applicant_id: str, 
    campaign_id: str,
    max_retries: int = 3
) -> Dict[str, Any]:
    """Startet Call mit Retry-Logik"""
    
    for attempt in range(max_retries):
        try:
            self.logger.info(f"Call attempt {attempt + 1}/{max_retries}")
            return self.start_call(applicant_id, campaign_id)
            
        except Exception as e:
            self.logger.error(f"Attempt {attempt + 1} failed: {e}")
            
            if attempt == max_retries - 1:
                self.logger.error("All retry attempts failed")
                raise
            
            # Exponential Backoff
            wait_time = 2 ** attempt
            self.logger.info(f"Retrying in {wait_time}s...")
            time.sleep(wait_time)
```

---

### 3.3 Cost Tracking

**Neue Datei:** `backend/src/utils/cost_tracker.py`

```python
"""Cost Tracking für ElevenLabs Calls"""
from pathlib import Path
import json
from datetime import datetime

class CostTracker:
    """Trackt Kosten von ElevenLabs Calls"""
    
    COST_PER_MINUTE = 0.20  # USD
    
    def __init__(self, log_file: str = "Output_ordner/costs.json"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def track_call(
        self, 
        conversation_id: str, 
        duration_seconds: int,
        applicant_id: str = None
    ):
        """Logged einen Call und berechnet Kosten"""
        
        duration_minutes = duration_seconds / 60
        cost_usd = duration_minutes * self.COST_PER_MINUTE
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "conversation_id": conversation_id,
            "applicant_id": applicant_id,
            "duration_seconds": duration_seconds,
            "duration_minutes": round(duration_minutes, 2),
            "cost_usd": round(cost_usd, 4)
        }
        
        # Lade existing
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"calls": [], "total_cost_usd": 0}
        
        # Append
        data["calls"].append(entry)
        data["total_cost_usd"] = round(
            data["total_cost_usd"] + cost_usd, 4
        )
        
        # Save
        with open(self.log_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return entry
```

---

## 📊 Meilensteine & Checkpoints

| Meilenstein | Geschätzte Zeit | Checkpoint |
|-------------|-----------------|------------|
| **1.1** Master Prompt Integration | 30 min | Dry-Run funktioniert |
| **1.2** Phase-Prompts Integration | 45 min | KB > 15.000 Zeichen |
| **1.3** Erster echter Call | 15 min | Call im Dashboard sichtbar |
| **2.1** Transkript-Abruf | 30 min | Transkript gespeichert |
| **2.2** Output-Speicherung | 20 min | Alle Dateien im calls/ Ordner |
| **2.3** Logging | 20 min | Logs in Output_ordner/logs/ |
| **3.1** Webhook (optional) | 1h | Webhook empfängt Events |
| **3.2** Retries (optional) | 30 min | Retry-Logik funktioniert |
| **3.3** Cost Tracking (optional) | 30 min | costs.json wird gefüllt |

**Gesamt (MVP):** 2-3 Stunden  
**Gesamt (Full):** 4-5 Stunden

---

## 🎯 Nächster konkreter Schritt

**JETZT starten:** Phase 1.1 - Master Prompt Integration

1. Öffne `backend/src/orchestrator/call_orchestrator.py`
2. Füge `_load_master_prompt()` Methode hinzu
3. Rufe sie in `start_call()` auf
4. Übergebe an `elevenlabs_client.start_conversation()`
5. Teste mit `test_dry_run.py`

**Bereit zum Loslegen?** 🚀

---

**Erstellt:** 29. Oktober 2025  
**Letztes Update:** Nach erfolgreichem API-Test

