"""Call Orchestrator - Steuert den kompletten Voice-Recruiting-Ablauf"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ..data_sources.base import DataSource
from ..aggregator.unified_aggregator import UnifiedAggregator
from ..aggregator.knowledge_base_builder import KnowledgeBaseBuilder
from ..elevenlabs.voice_client import ElevenLabsVoiceClient
from ..telephony.base import ConversationTransport
from ..config import Settings
from ..utils.logger import setup_logger


def safe_print(text: str):
    """Gibt Text aus und fängt Unicode-Fehler ab"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: Entferne Emojis
        import re
        text_no_emoji = re.sub(r'[^\x00-\x7F]+', '', text)
        print(text_no_emoji)


class CallOrchestrator:
    """
    Orchestriert den kompletten Ablauf eines Voice-Recruiting-Calls:
    1. Daten laden
    2. Questions.json generieren (optional)
    3. Daten aggregieren
    4. ElevenLabs Call starten
    """

    def __init__(
        self,
        data_source: DataSource,
        conversation_client: ConversationTransport,
        settings: Settings
    ):
        """
        Initialisiert Orchestrator.
        
        Args:
            data_source: DataSource für Bewerber-/Firmendaten
            conversation_client: Transport Layer (WebRTC/Twilio/etc.)
            settings: Konfiguration
        """
        self.data_source = data_source
        self.conversation_client = conversation_client
        self.settings = settings
        
        self.aggregator = UnifiedAggregator(
            prompts_dir=settings.get_prompts_dir_path()
        )
        self.kb_builder = KnowledgeBaseBuilder(
            prompts_dir=settings.get_prompts_dir_path()
        )
        self.logger = setup_logger("call_orchestrator")

    def start_call(
        self, 
        applicant_id: str, 
        campaign_id: str,
        phase: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Startet einen kompletten Voice-Recruiting-Call.
        
        Args:
            applicant_id: ID des Bewerbers
            campaign_id: ID der Kampagne
            phase: Optional: Nur bestimmte Phase starten (1-4)
            
        Returns:
            Dict mit Ergebnis (conversation_id, status, etc.)
        """
        self.logger.info(f"Starting call - Applicant: {applicant_id}, Campaign: {campaign_id}, Phase: {phase or 'All'}")
        
        try:
            print(f"\n{'='*70}")
            safe_print(f"🚀 Starte Voice-Recruiting-Call")
            print(f"{'='*70}")
            print(f"Bewerber-ID: {applicant_id}")
            print(f"Kampagnen-ID: {campaign_id}")
            print(f"Phase: {phase or 'Alle (1-4)'}")
            print(f"{'='*70}\n")

            # Step 1: Daten laden
            safe_print("📂 Schritt 1: Lade Daten...")
            applicant = self.data_source.get_applicant_profile(applicant_id)
            address = self.data_source.get_applicant_address(applicant_id)
            company = self.data_source.get_company_profile(campaign_id)
            protocol = self.data_source.get_conversation_protocol(campaign_id)
            
            print(f"   ✓ Bewerber: {applicant.get('first_name')} {applicant.get('last_name')}")
            print(f"   ✓ Adresse: {address.get('city', 'N/A')}")
            print(f"   ✓ Unternehmen: {company.get('name', 'N/A')}")
            print(f"   ✓ Protokoll: {len(protocol.get('pages', []))} Seiten")

            # Step 2: Questions.json generieren (optional)
            questions_json = self._load_or_generate_questions(protocol)
            
            # Step 3: Daten aggregieren
            safe_print("\n🔄 Schritt 3: Aggregiere Daten...")
            phase_data = self._aggregate_all_phases(
                applicant, address, company, questions_json
            )
            
            # Step 4: Knowledge Bases erstellen
            safe_print("\n📝 Schritt 4: Erstelle Knowledge Bases...")
            knowledge_bases = self._build_knowledge_bases(phase_data)
            
            # Step 4.5: Master Prompt laden
            master_prompt = self._load_master_prompt()
            
            # Step 5: ElevenLabs Call starten
            safe_print("\n📞 Schritt 5: Starte ElevenLabs Call...")
            
            if phase:
                # Nur bestimmte Phase
                result = self._start_single_phase(phase, knowledge_bases, master_prompt)
            else:
                # Alle Phasen sequenziell
                result = self._start_multi_phase_call(knowledge_bases, master_prompt, applicant_id)
            
            self.logger.info(f"Call started successfully - Conversation ID: {result.get('conversation_id')}")
            
            print(f"\n{'='*70}")
            print(f"✅ Call erfolgreich gestartet!")
            print(f"{'='*70}\n")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Call failed: {str(e)}", exc_info=True)
            raise

    def _load_master_prompt(self) -> str:
        """Lädt Master Prompt aus Masterprompt.md"""
        prompt_file = self.settings.get_prompts_dir_path() / "Masterprompt.md"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Master Prompt nicht gefunden: {prompt_file}")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        safe_print(f"   ✓ Master Prompt geladen: {len(content)} Zeichen")
        return content

    def _load_or_generate_questions(self, protocol: Dict[str, Any]) -> Dict[str, Any]:
        """Lädt questions.json oder generiert es via TypeScript Tool"""
        print("\n📋 Schritt 2: Lade/Generiere questions.json...")
        
        questions_path = self.settings.get_questions_json_path()
        
        # Prüfe ob generieren gewünscht
        if self.settings.generate_questions:
            print("   🔨 Generiere questions.json via TypeScript Tool...")
            self._run_typescript_tool()
        
        # Lade questions.json
        if questions_path.exists():
            with open(questions_path, 'r', encoding='utf-8') as f:
                questions_json = json.load(f)
            safe_print(f"   ✓ questions.json geladen: {len(questions_json.get('questions', []))} Fragen")
            return questions_json
        else:
            safe_print("   ⚠️  Warnung: questions.json nicht gefunden - verwende Fallback")
            return {"_meta": {}, "questions": []}

    def _run_typescript_tool(self):
        """Führt TypeScript Question Builder Tool aus"""
        tool_path = self.settings.get_typescript_tool_path()
        
        if not tool_path.exists():
            raise FileNotFoundError(f"TypeScript Tool nicht gefunden: {tool_path}")
        
        try:
            # Wechsle ins Tool-Verzeichnis und führe npm start aus
            result = subprocess.run(
                ["npm", "start"],
                cwd=tool_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"   ⚠️  Tool-Ausführung fehlgeschlagen:\n{result.stderr}")
            else:
                print("   ✓ TypeScript Tool erfolgreich ausgeführt")
                
        except subprocess.TimeoutExpired:
            print("   ⚠️  Tool-Timeout (>60s)")
        except Exception as e:
            print(f"   ⚠️  Fehler beim Ausführen des Tools: {e}")

    def _aggregate_all_phases(
        self,
        applicant: Dict[str, Any],
        address: Dict[str, Any],
        company: Dict[str, Any],
        questions_json: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Aggregiert Daten für alle Phasen"""
        
        phase_1 = self.aggregator.aggregate_phase_1(applicant, address)
        print(f"   ✓ Phase 1: {len(phase_1)} Variablen")
        
        phase_2 = self.aggregator.aggregate_phase_2(company)
        print(f"   ✓ Phase 2: {len(phase_2)} Variablen")
        
        phase_3 = self.aggregator.aggregate_phase_3(questions_json)
        print(f"   ✓ Phase 3: {phase_3['total_questions']} Fragen")
        
        phase_4 = self.aggregator.aggregate_phase_4(applicant)
        print(f"   ✓ Phase 4: {len(phase_4)} Variablen")
        
        return {
            "phase_1": phase_1,
            "phase_2": phase_2,
            "phase_3": phase_3,
            "phase_4": phase_4
        }

    def _build_knowledge_bases(
        self, 
        phase_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, str]:
        """Erstellt Knowledge Bases für alle Phasen"""
        
        kb_1 = self.kb_builder.build_phase_1(phase_data["phase_1"])
        print(f"   ✓ Phase 1 KB: {len(kb_1)} Zeichen")
        
        kb_2 = self.kb_builder.build_phase_2(phase_data["phase_2"])
        print(f"   ✓ Phase 2 KB: {len(kb_2)} Zeichen")
        
        kb_3 = self.kb_builder.build_phase_3(phase_data["phase_3"]["questions"])
        print(f"   ✓ Phase 3 KB: {len(kb_3)} Zeichen")
        
        kb_4 = self.kb_builder.build_phase_4(phase_data["phase_4"])
        print(f"   ✓ Phase 4 KB: {len(kb_4)} Zeichen")
        
        return {
            "phase_1": kb_1,
            "phase_2": kb_2,
            "phase_3": kb_3,
            "phase_4": kb_4
        }

    def _start_single_phase(
        self, 
        phase: int, 
        knowledge_bases: Dict[str, str],
        system_prompt: str
    ) -> Dict[str, Any]:
        """Startet einen einzelnen Phase-Call"""
        
        kb = knowledge_bases[f"phase_{phase}"]
        
        result = self.conversation_client.start_conversation(
            agent_id=self.settings.elevenlabs_agent_id,
            knowledge_base=kb,
            system_prompt=system_prompt
        )
        
        print(f"   ✓ Phase {phase} gestartet: {result['conversation_id']}")
        
        return {
            "phase": phase,
            "conversation_id": result["conversation_id"],
            "status": result["status"]
        }

    def _start_multi_phase_call(
        self, 
        knowledge_bases: Dict[str, str],
        system_prompt: str,
        applicant_id: str
    ) -> Dict[str, Any]:
        """Startet alle Phasen sequenziell"""
        
        # Für MVP: Kombiniere alle Knowledge Bases
        # In Produktion: Separate Calls mit Phase-Transition
        
        combined_kb = "\n\n".join([
            "=" * 80,
            "MASTER KNOWLEDGE BASE - ALLE PHASEN",
            "=" * 80,
            knowledge_bases["phase_1"],
            knowledge_bases["phase_2"],
            knowledge_bases["phase_3"],
            knowledge_bases["phase_4"]
        ])
        
        result = self.conversation_client.start_conversation(
            agent_id=self.settings.elevenlabs_agent_id,
            knowledge_base=combined_kb,
            system_prompt=system_prompt
        )
        
        print(f"   ✓ Multi-Phase Call gestartet: {result['conversation_id']}")
        
        # Speichere Call-Ergebnisse
        self._save_call_results(
            conversation_id=result['conversation_id'],
            applicant_id=applicant_id,
            knowledge_base=combined_kb
        )
        
        return {
            "phases": "1-4",
            "conversation_id": result["conversation_id"],
            "status": result["status"],
            "knowledge_base_size": len(combined_kb)
        }

    def _save_call_results(
        self,
        conversation_id: str,
        applicant_id: str,
        knowledge_base: str,
        transcript: Optional[str] = None
    ):
        """Speichert Call-Ergebnisse in Output_ordner/calls/"""
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
        
        # Transkript (falls vorhanden)
        if transcript:
            with open(output_dir / f"{conversation_id}_transcript.txt", "w", encoding="utf-8") as f:
                f.write(transcript)
        
        safe_print(f"   ✓ Ergebnisse gespeichert: {conversation_id}_*")

