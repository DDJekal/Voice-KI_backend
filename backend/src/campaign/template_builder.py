"""Template Builder - Erstellt KB Templates mit Variablen-Platzhaltern"""

from typing import Dict, Any
from pathlib import Path


class TemplateBuilder:
    """
    Erstellt Knowledge Base Templates mit {{Platzhaltern}} statt festen Werten.
    
    Diese Templates können später mit Bewerberdaten gefüllt werden,
    ohne das gesamte Campaign-Setup erneut durchzuführen.
    """
    
    def __init__(self, prompts_dir: Path = None):
        """
        Args:
            prompts_dir: Pfad zu VoiceKI _prompts/ Ordner
        """
        if prompts_dir is None:
            prompts_dir = Path("../VoiceKI _prompts")
        self.prompts_dir = prompts_dir
    
    def _load_phase_prompt(self, phase_number: int) -> str:
        """Lädt Phase-Prompt aus Phase_{number}.md"""
        prompt_file = self.prompts_dir / f"Phase_{phase_number}.md"
        
        if not prompt_file.exists():
            return f"# Phase {phase_number}\n(Prompt-Datei nicht gefunden)"
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def build_phase_1_template(self, company_data: Dict[str, Any]) -> str:
        """
        Erstellt Template für Phase 1: Begrüßung & Kontaktdaten.
        
        Verwendet Variablen-Platzhalter für Bewerberdaten:
        - {{first_name}}, {{last_name}}
        - {{telephone}}, {{email}}
        - {{street}}, {{house_number}}, {{postal_code}}, {{city}}
        
        Args:
            company_data: Company-Profil (für Rolle/Position)
        
        Returns:
            Template-String mit Platzhaltern
        """
        phase_prompt = self._load_phase_prompt(1)
        
        template = f"""{'='*80}
PHASE 1: BEGRÜSSUNG & KONTAKTDATEN
{'='*80}

{phase_prompt}

{'='*80}
DATEN FÜR DIESE PHASE
{'='*80}

BEWERBERDATEN:
Name: {{{{first_name}}}} {{{{last_name}}}}
Telefon: {{{{telephone}}}}
Email: {{{{email}}}}

ADRESSE-BEHANDLUNG:
Die Adresse wird basierend auf dem Gesprächsprotokoll abgefragt.
Falls im Protokoll gefordert, wird die Adresse erfragt:
- Straße: {{{{street}}}}
- Hausnummer: {{{{house_number}}}}
- PLZ: {{{{postal_code}}}}
- Ort: {{{{city}}}}

Falls Adresse vorhanden (aus Daten):
"Ich habe Ihre Adresse als {{{{street}}}} {{{{house_number}}}}, {{{{postal_code}}}} {{{{city}}}} notiert. Ist das korrekt?"

Falls Adresse nicht vorhanden:
"Nennen Sie mir bitte Ihre vollständige Adresse mit Straße, Hausnummer, PLZ und Ort."

ROLLE:
{{{{campaignrole_title}}}}

DATENSCHUTZ-EINWILLIGUNG:
{{{{privacy_text}}}}
"""
        return template
    
    def build_phase_2_template(self, company_data: Dict[str, Any]) -> str:
        """
        Erstellt Template für Phase 2: Unternehmensvorstellung.
        
        Company-Daten sind fix (pro Campaign), daher direkt eingebettet.
        
        Args:
            company_data: Company-Profil
        
        Returns:
            Template mit Company-Daten
        """
        phase_prompt = self._load_phase_prompt(2)
        
        template = f"""{'='*80}
PHASE 2: UNTERNEHMENSVORSTELLUNG
{'='*80}

{phase_prompt}

{'='*80}
DATEN FÜR DIESE PHASE
{'='*80}

UNTERNEHMEN:
Name: {company_data.get('name', '')}
Größe: ca. {company_data.get('size', '')} Mitarbeitende
Standort: {company_data.get('address', '')}

VORTEILE & BENEFITS:
{company_data.get('benefits', '')}

AKTUELLE PRIORITÄTEN:
{company_data.get('priority_areas', 'Keine spezifischen Prioritäten angegeben')}

POSITION:
{{{{campaignrole_title}}}} am Standort {{{{campaignlocation_label}}}}
"""
        return template
    
    def build_phase_3_template(self, questions_json: Dict[str, Any]) -> str:
        """
        Erstellt Template für Phase 3: Fragenkatalog.
        
        Questions.json wird komplett eingebettet (bereits statisch pro Campaign).
        
        Args:
            questions_json: Das komplette questions.json
        
        Returns:
            Template mit questions.json
        """
        phase_prompt = self._load_phase_prompt(3)
        
        questions = questions_json.get("questions", [])
        
        template = f"""{'='*80}
PHASE 3: FRAGENKATALOG
{'='*80}

{phase_prompt}

{'='*80}
FRAGEN FÜR DIESE PHASE
{'='*80}

"""
        
        # Gruppiere nach Kategorie
        by_category = self._group_by_category(questions_json)
        
        # Definierte Reihenfolge
        category_order = [
            ("identifikation", "IDENTIFIKATION & BESTÄTIGUNG"),
            ("kontaktinformationen", "KONTAKTDATEN"),
            ("standardqualifikationen", "STANDARDQUALIFIKATIONEN (GATE)"),
            ("info", "UNTERNEHMENSVORSTELLUNG & STELLENINFOS"),
            ("standort", "STANDORTE"),
            ("einsatzbereiche", "EINSATZBEREICHE & ABTEILUNGEN"),
            ("rahmenbedingungen", "RAHMENBEDINGUNGEN"),
            ("zusaetzliche_informationen", "ZUSÄTZLICHE INFORMATIONEN")
        ]
        
        # Statistik
        total_by_category = {cat: len(by_category.get(cat, [])) for cat, _ in category_order}
        template += "ÜBERSICHT:\n"
        for cat, name in category_order:
            count = total_by_category.get(cat, 0)
            if count > 0:
                template += f"  {name}: {count} Frage(n)\n"
        template += "\n"
        
        # Kategorien durchgehen
        for cat_key, cat_name in category_order:
            if cat_key not in by_category or len(by_category[cat_key]) == 0:
                continue
            
            template += f"\n{'='*70}\n"
            template += f"{cat_name}\n"
            template += f"{'='*70}\n\n"
            
            if cat_key == "standardqualifikationen":
                template += "WICHTIG: Gate-Questions! Bei NEIN auf Muss-Kriterium → Gespräch höflich beenden.\n\n"
            
            # Fragen formatieren
            for q in by_category[cat_key]:
                template += self._format_question_for_template(q)
                template += "\n" + "-"*60 + "\n\n"
        
        return template
    
    def build_phase_4_template(self, company_data: Dict[str, Any]) -> str:
        """
        Erstellt Template für Phase 4: Beruflicher Werdegang & Abschluss.
        
        Verwendet Variablen für Bewerber-Name.
        
        Args:
            company_data: Company-Profil
        
        Returns:
            Template mit Platzhaltern
        """
        phase_prompt = self._load_phase_prompt(4)
        
        template = f"""{'='*80}
PHASE 4: BERUFLICHER WERDEGANG & GESPRÄCHSABSCHLUSS
{'='*80}

{phase_prompt}

{'='*80}
DATEN FÜR DIESE PHASE
{'='*80}

BEWERBER:
{{{{first_name}}}} {{{{last_name}}}}

AUSBILDUNG/ABSCHLUSS:
Wird im Gespräch erfragt (siehe Phase 4 Prompt).

LETZTE DREI ARBEITGEBER:
Werden im Gespräch erfragt (Name + Zeitraum).

RÜCKMELDUNG-ZEITFENSTER:
{{{{handoffwindow}}}}

UNTERNEHMEN:
{company_data.get('name', '')}
"""
        return template
    
    def _group_by_category(self, questions_json: Dict) -> Dict[str, list]:
        """Gruppiert Fragen nach Kategorie"""
        by_category = {}
        questions = questions_json.get("questions", [])
        
        for q in questions:
            if not isinstance(q, dict):
                continue
            
            category = q.get("category", "zusaetzliche_informationen")
            
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(q)
        
        return by_category
    
    def _format_question_for_template(self, question: Dict[str, Any]) -> str:
        """Formatiert eine einzelne Frage für Template"""
        output = f"FRAGE-ID: {question.get('id', 'unknown')}\n"
        output += f"Typ: {question.get('type', 'text')}\n"
        output += f"Pflicht: {'JA' if question.get('required') else 'NEIN'}\n"
        output += f"Priorität: {question.get('priority', 3)}\n\n"
        
        output += f"Frage:\n{question.get('question', '')}\n\n"
        
        # Gate-Config (falls vorhanden)
        if question.get("gate_config"):
            gc = question["gate_config"]
            output += "\n" + "="*60 + "\n"
            output += "⚠️  GATE-LOGIK\n"
            output += "="*60 + "\n"
            
            if gc.get("is_gate"):
                output += "▸ Dies ist eine Gate-Question\n"
                if gc.get("has_alternatives"):
                    output += "▸ Hat Alternativen\n"
                else:
                    output += "▸ KEINE Alternativen - bei NEIN Gespräch beenden\n"
            
            output += "="*60 + "\n\n"
        
        # Optionen
        if question.get("options"):
            options = question["options"]
            if len(options) <= 6:
                output += "Optionen:\n"
                for opt in options:
                    output += f"  - {opt}\n"
            else:
                output += f"Optionen: {len(options)} Optionen vorhanden\n"
                output += "WICHTIG: Nutze Pre-Check + Clustering!\n"
        
        return output
    
    def build_all_templates(
        self, 
        company_data: Dict[str, Any], 
        questions_json: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Erstellt alle 4 Phase-Templates.
        
        Args:
            company_data: Company-Profil
            questions_json: Questions.json
        
        Returns:
            Dict mit phase_1 bis phase_4 Templates
        """
        return {
            "phase_1": self.build_phase_1_template(company_data),
            "phase_2": self.build_phase_2_template(company_data),
            "phase_3": self.build_phase_3_template(questions_json),
            "phase_4": self.build_phase_4_template(company_data)
        }

