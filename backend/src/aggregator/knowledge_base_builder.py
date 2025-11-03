"""Knowledge Base Builder - Wandelt aggregierte Daten in ElevenLabs-Format"""

from typing import Dict, Any, List
from pathlib import Path


class KnowledgeBaseBuilder:
    """
    Erstellt natürlichsprachliche Knowledge Bases für ElevenLabs
    aus strukturierten Daten.
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

    def build_phase_1(self, data: Dict[str, Any]) -> str:
        """
        Erstellt Knowledge Base für Phase 1: Begrüßung & Kontaktdaten.
        
        Args:
            data: Aggregierte Daten aus UnifiedAggregator.aggregate_phase_1()
            
        Returns:
            Natürlichsprachlicher Text für ElevenLabs
        """
        # Lade Phase-Prompt
        phase_prompt = self._load_phase_prompt(1)
        
        # Prüfe ob Adresse vorhanden ist
        has_address = bool(data.get('street', '').strip())
        
        kb = f"""{'='*80}
PHASE 1: BEGRÜSSUNG & KONTAKTDATEN
{'='*80}

{phase_prompt}

{'='*80}
DATEN FÜR DIESE PHASE
{'='*80}

BEWERBERDATEN:
Name: {data['candidatefirst_name']} {data['candidatelast_name']}
Telefon: {data['telephone']}
Email: {data['email']}

"""
        
        # Konditionale Adress-Behandlung
        if has_address:
            kb += f"""AKTUELLE ADRESSE (zu bestätigen):
{data['street']} {data['house_number']}, {data['postal_code']} {data['city']}

WICHTIG: Bestätige die Adresse mit dem Bewerber:
"Ich habe Ihre Adresse als {data['street']} {data['house_number']}, {data['postal_code']} {data['city']} notiert. Ist das korrekt?"
"""
        else:
            kb += """ADRESSE: NICHT VORHANDEN

WICHTIG: Frage die vollständige Adresse ab!
"Nennen Sie mir bitte Ihre vollständige Adresse mit Straße, Hausnummer, PLZ und Ort."

Erfasse einzeln:
1. Straße und Hausnummer
2. Postleitzahl
3. Ort
"""
        
        kb += f"""
ROLLE:
{data['rolle']}

DATENSCHUTZ-EINWILLIGUNG:
{data['privacy_text']}
"""
        return kb

    def build_phase_2(self, data: Dict[str, Any]) -> str:
        """
        Erstellt Knowledge Base für Phase 2: Unternehmensvorstellung.
        
        Args:
            data: Aggregierte Daten aus UnifiedAggregator.aggregate_phase_2()
            
        Returns:
            Natürlichsprachlicher Text für ElevenLabs
        """
        # Lade Phase-Prompt
        phase_prompt = self._load_phase_prompt(2)
        
        kb = f"""{'='*80}
PHASE 2: UNTERNEHMENSVORSTELLUNG
{'='*80}

{phase_prompt}

{'='*80}
DATEN FÜR DIESE PHASE
{'='*80}

UNTERNEHMEN:
Name: {data['companyname']}
Größe: ca. {data['companysize']} Mitarbeitende
Standort: {data['campaignlocation_label']}

VORTEILE & BENEFITS:
{data['companypitch']}

AKTUELLE PRIORITÄTEN:
{data['companypriorities']}

POSITION:
{data['campaignrole_title']}
"""
        return kb

    def build_phase_3(self, questions_json: Dict[str, Any]) -> str:
        """
        Erstellt Knowledge Base für Phase 3: Fragenkatalog mit Kategorisierung.
        
        Args:
            questions_json: Das komplette questions.json
            
        Returns:
            Strukturierter Text mit Anweisungen für Voice Agent nach Kategorien
        """
        # Lade Phase-Prompt
        phase_prompt = self._load_phase_prompt(3)
        
        questions = questions_json.get("questions", [])
        
        # Header mit neuer Struktur
        kb = f"""{'='*80}
PHASE 3: FRAGENKATALOG
{'='*80}

{phase_prompt}

{'='*80}
FRAGEN FÜR DIESE PHASE
{'='*80}

"""
        
        # Gruppiere nach Kategorie (mit Fallback auf alte Gruppen)
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
        kb += "ÜBERSICHT:\n"
        for cat, name in category_order:
            count = total_by_category.get(cat, 0)
            if count > 0:
                kb += f"  {name}: {count} Frage(n)\n"
        kb += "\n"
        
        # Kategorien durchgehen
        for cat_key, cat_name in category_order:
            if cat_key not in by_category or len(by_category[cat_key]) == 0:
                continue
            
            kb += f"\n{'='*70}\n"
            kb += f"{cat_name}\n"
            kb += f"{'='*70}\n\n"
            
            # Spezielle Behandlung für bestimmte Kategorien
            if cat_key == "standardqualifikationen":
                kb += "WICHTIG: Gate-Questions! Bei NEIN auf Muss-Kriterium → Gespräch höflich beenden.\n\n"
                kb += self._format_question_section(by_category[cat_key])
            elif cat_key == "info":
                kb += self._format_info_section(by_category[cat_key])
            else:
                kb += self._format_question_section(by_category[cat_key])
        
        # NEU: Context-Rules hinzufügen (wenn Policies angewendet wurden)
        if questions_json.get("_meta", {}).get("policies_applied"):
            kb += self._build_conversation_context_rules(questions_json)
        
        return kb

    def build_phase_4(self, data: Dict[str, Any]) -> str:
        """
        Erstellt Knowledge Base für Phase 4: Beruflicher Werdegang.
        
        Args:
            data: Aggregierte Daten aus UnifiedAggregator.aggregate_phase_4()
            
        Returns:
            Natürlichsprachlicher Text für ElevenLabs
        """
        # Lade Phase-Prompt
        phase_prompt = self._load_phase_prompt(4)
        
        kb = f"""{'='*80}
PHASE 4: BERUFLICHER WERDEGANG & GESPRÄCHSABSCHLUSS
{'='*80}

{phase_prompt}

{'='*80}
DATEN FÜR DIESE PHASE
{'='*80}

BEWERBER:
{data['candidatefirst_name']} {data['candidatelast_name']}

ZUSÄTZLICHE INFORMATIONEN:
{data.get('information', 'Keine zusätzlichen Informationen vorhanden')}

RÜCKMELDUNG-ZEITFENSTER:
{data.get('handoffwindow', 'Das Recruiting meldet sich innerhalb von 48 Stunden')}
"""
        return kb

    def _format_question(self, question: Dict[str, Any]) -> str:
        """Formatiert eine einzelne Frage für die Knowledge Base"""
        output = f"FRAGE-ID: {question['id']}\n"
        output += f"Typ: {question['type']}\n"
        output += f"Pflicht: {'JA' if question.get('required') else 'NEIN'}\n"
        output += f"Priorität: {question.get('priority', 3)}\n\n"
        
        output += f"Frage:\n{question['question']}\n\n"
        
        # Gate-Config (falls vorhanden)
        if question.get("gate_config"):
            gc = question["gate_config"]
            output += "\n" + "="*60 + "\n"
            output += "⚠️  GATE-LOGIK\n"
            output += "="*60 + "\n"
            
            if gc.get("is_gate"):
                output += "▸ Dies ist eine Gate-Question\n"
                if gc.get("has_alternatives"):
                    output += "▸ Hat Alternativen (siehe unten)\n"
                    if gc.get("alternative_question_ids"):
                        output += f"▸ Alternative IDs: {', '.join(gc['alternative_question_ids'])}\n"
                else:
                    output += "▸ KEINE Alternativen verfügbar\n"
                    output += "▸ Bei NEIN → Gespräch sofort beenden\n"
                
                if gc.get("end_message"):
                    output += f"\nENDE-NACHRICHT bei NEIN:\n\"{gc['end_message']}\"\n"
                
                # NEU: Slot-Requirements
                if gc.get("requires_slots"):
                    output += f"▸ Benötigt Slots: {', '.join(gc['requires_slots'])}\n"
                
                if gc.get("condition"):
                    output += f"▸ Bedingung: {gc['condition']}\n"
            
            if gc.get("is_alternative"):
                output += f"▸ Dies ist eine ALTERNATIVE zu: {gc.get('alternative_for')}\n"
                if gc.get("can_satisfy_gate"):
                    output += "▸ Kann Gate-Kriterium erfüllen bei JA\n"
                if gc.get("final_alternative"):
                    output += "▸ ⚠️  LETZTE Alternative - bei NEIN Gespräch beenden!\n"
                    if gc.get("end_message_if_all_no"):
                        output += f"\nENDE-NACHRICHT:\n\"{gc['end_message_if_all_no']}\"\n"
            
            # NEU: Context-Triggers
            if gc.get("context_triggers"):
                ct = gc["context_triggers"]
                output += "\n▸ KEYWORD-TRIGGER:\n"
                if ct.get("keywords_to_follow_up"):
                    keywords = ct["keywords_to_follow_up"]
                    output += f"  Wenn Kandidat erwähnt: {', '.join(keywords)}\n"
                    output += "  → Sofort vertiefen und nachfragen!\n"
            
            output += "="*60 + "\n\n"
        
        # NEU: Slot-Config
        if question.get("slot_config"):
            sc = question["slot_config"]
            output += "\n" + "="*60 + "\n"
            output += "✨  SLOT-TRACKING\n"
            output += "="*60 + "\n"
            output += f"▸ Füllt Slot: {sc['fills_slot']}\n"
            output += f"▸ Erforderlich: {'JA' if sc.get('required') else 'NEIN'}\n"
            output += f"▸ Confidence-Schwelle: {sc.get('confidence_threshold', 0.8)}\n"
            
            if sc.get("validation"):
                val = sc["validation"]
                if val.get("keywords_yes"):
                    output += f"▸ Positive Signale: {', '.join(val['keywords_yes'])}\n"
                if val.get("keywords_no"):
                    output += f"▸ Negative Signale: {', '.join(val['keywords_no'])}\n"
            
            output += "="*60 + "\n\n"
        
        # NEU: Conversation-Hints
        if question.get("conversation_hints"):
            ch = question["conversation_hints"]
            output += "\n" + "="*60 + "\n"
            output += "💬  GESPRÄCHSFÜHRUNG\n"
            output += "="*60 + "\n"
            
            if ch.get("on_unclear_answer"):
                output += f"▸ Bei unklarer Antwort:\n  \"{ch['on_unclear_answer']}\"\n\n"
            
            if ch.get("on_negative_answer"):
                output += f"▸ Bei NEIN-Antwort:\n  \"{ch['on_negative_answer']}\"\n\n"
            
            if ch.get("confidence_boost_phrases"):
                phrases = ch["confidence_boost_phrases"][:5]  # Max 5 zeigen
                output += f"▸ Klare Signale: {', '.join(phrases)}\n"
            
            if ch.get("diversify_after"):
                output += f"▸ WICHTIG: Nach dieser Frage keine weiteren {ch['diversify_after']}-Fragen!\n"
            
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
        
        # Conversation Flow
        if question.get("conversation_flow"):
            cf = question["conversation_flow"]
            output += "\nVORGEHEN (Conversation Flow):\n"
            
            if "pre_check" in cf:
                pc = cf["pre_check"]
                output += f"1. Pre-Check: \"{pc['question']}\"\n"
                output += f"   - Bei JA → {pc['on_yes']}\n"
                output += f"   - Bei NEIN → {pc['on_no']}\n"
            
            if "open_question" in cf:
                oq = cf["open_question"]
                output += f"2. Offene Frage: \"{oq['question']}\"\n"
                if oq.get("allow_fuzzy_match"):
                    output += "   - Fuzzy Matching erlaubt (ähnliche Begriffe OK)\n"
            
            if "clustered_options" in cf:
                co = cf["clustered_options"]
                if "presentation_hint" in co:
                    output += f"3. Einleitung: \"{co['presentation_hint']}\"\n"
                if "categories" in co:
                    output += "4. Kategorien:\n"
                    for cat in co["categories"]:
                        output += f"   - {cat['label']}: {len(cat['options'])} Optionen\n"
        
        # Bedingungen
        if question.get("conditions"):
            output += "\nBEDINGUNGEN (nur fragen wenn):\n"
            for cond in question["conditions"]:
                if "when" in cond:
                    when = cond["when"]
                    output += f"  • Feld '{when['field']}' {when['op']} {when.get('value', '')}\n"
        
        # Hilfetext
        if question.get("help_text"):
            output += f"\nHINWEIS: {question['help_text']}\n"
        
        if question.get("context"):
            output += f"\nKONTEXT: {question['context']}\n"
        
        return output

    def _group_by_category(self, questions_json: Dict) -> Dict[str, List[Dict]]:
        """Gruppiert Fragen nach Kategorie (mit Fallback auf alte 'group')"""
        by_category = {}
        questions = questions_json.get("questions", [])
        
        for q in questions:
            if not isinstance(q, dict):
                continue
                
            # Neue Kategorien nutzen, falls vorhanden
            category = q.get("category", None)
            
            # Fallback: Mapping von alten "group" zu Kategorien
            if not category:
                category = self._map_group_to_category(q)
            
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(q)
        
        return by_category
    
    def _map_group_to_category(self, question: Dict) -> str:
        """Mappt alte 'group' Werte zu neuen Kategorien."""
        group = question.get("group", "").lower()
        question_text = question.get("question", "").lower()
        q_type = question.get("type", "")
        is_required = question.get("required", False)
        
        # Identifikation (Bestätigungsfragen)
        if ("adresse" in question_text and 
            ("korrekt" in question_text or "bestät" in question_text)):
            return "identifikation"
        
        # Kontaktinformationen (Erfassung)
        if group == "kontakt" or "telefon" in question_text or "e-mail" in question_text:
            # Aber nicht Bestätigungsfragen
            if not ("korrekt" in question_text or "bestät" in question_text):
                return "kontaktinformationen"
        
        # Standardqualifikationen (Gate)
        if ((group == "qualifikation" and is_required) or
            "zwingend" in question_text or 
            "examen" in question_text or
            "abschluss" in question_text):
            return "standardqualifikationen"
        
        # Info
        if q_type == "info" or question_text.startswith("!!!"):
            return "info"
        
        # Standort
        if group == "standort":
            return "standort"
        
        # Einsatzbereiche
        if group == "einsatzbereich":
            return "einsatzbereiche"
        
        # Rahmenbedingungen
        if group == "rahmen":
            return "rahmenbedingungen"
        
        # Default
        return "zusaetzliche_informationen"
    
    def _format_question_section(self, questions: List[Dict]) -> str:
        """Formatiert reguläre Fragen mit Details."""
        # Sortiere: required=true zuerst, dann nach Priorität
        sorted_q = sorted(questions, key=lambda x: (
            not x.get('required', False),
            x.get('priority', 3),
            x.get('position', 999)
        ))
        
        section = ""
        for q in sorted_q:
            section += self._format_question(q)
            section += "\n" + "-"*60 + "\n\n"
        
        return section
    
    def _format_info_section(self, info_items: List[Dict]) -> str:
        """Formatiert Info-Items (keine Fragen, nur Informationen)."""
        section = "WICHTIG: Dies sind INFORMATIONEN für den Bewerber.\n"
        section += "KEINE Fragen stellen! Format: 'Ich möchte Ihnen noch mitteilen...'\n\n"
        
        for idx, item in enumerate(info_items, 1):
            section += f"INFO {idx}:\n"
            section += f"{item.get('question', '')}\n\n"
            section += "-" * 60 + "\n\n"
        
        return section
    
    def _build_conversation_context_rules(self, questions_json: Dict[str, Any]) -> str:
        """
        Generiert Context-Rules-Sektion für natürliche Gesprächsführung.
        
        Diese Regeln werden aus den Policy-enhanced Questions extrahiert
        und als allgemeine Leitlinien für ElevenLabs formuliert.
        """
        # Sammle alle Slots aus Fragen
        required_slots = []
        optional_slots = []
        keyword_triggers = {}
        
        for q in questions_json.get("questions", []):
            if q.get("slot_config"):
                sc = q["slot_config"]
                slot_name = sc["fills_slot"]
                if sc.get("required"):
                    required_slots.append(slot_name)
                else:
                    optional_slots.append(slot_name)
            
            # Sammle Keyword-Triggers
            if q.get("gate_config", {}).get("context_triggers", {}).get("keywords_to_follow_up"):
                keywords = q["gate_config"]["context_triggers"]["keywords_to_follow_up"]
                for kw in keywords:
                    if kw not in keyword_triggers:
                        keyword_triggers[kw] = []
                    keyword_triggers[kw].append(q["id"])
        
        rules = f"""

{'='*70}
🧠  KONTEXT-REGELN FÜR NATÜRLICHE GESPRÄCHSFÜHRUNG
{'='*70}

Diese Regeln gelten für ALLE Fragen in Phase 3 und sorgen für
natürliche, empathische und effektive Gespräche.

1. KEYWORD-SENSITIVITÄT (reagiere proaktiv!):
"""
        
        if keyword_triggers:
            for kw, question_ids in keyword_triggers.items():
                rules += f"   • \"{kw}\" erwähnt → Sofort vertiefen! (relevant für Fragen)\n"
        else:
            rules += "   • \"IMC\" / \"Intensiv\" / \"ITS\" → Vertiefe sofort\n"
            rules += "   • \"Teilzeit\" → Kläre Stunden/Woche direkt\n"
            rules += "   • \"Nachtdienst\" / \"Schichtdienst\" → Schichtmodell-Frage vorziehen\n"
            rules += "   • \"Familie\" / \"Kinder\" → Zeige Verständnis für Flexibilitätswünsche\n"
            rules += "   • \"Gehalt\" / \"Bezahlung\" → Auf spätere Phase verweisen\n"
        
        rules += f"""

2. CONFIDENCE & SLOT-TRACKING:
   
   Erforderliche Slots für Phase 3:
"""
        
        if required_slots:
            for slot in required_slots:
                rules += f"     ✓ {slot} (MUSS geklärt sein)\n"
        else:
            rules += "     ✓ qualifikation (MUSS geklärt sein)\n"
            rules += "     ✓ standort_praeferenz (MUSS geklärt sein)\n"
            rules += "     ✓ verfuegbarkeit_ab (MUSS geklärt sein)\n"
        
        if optional_slots:
            for slot in optional_slots[:5]:  # Max 5 zeigen
                rules += f"     ○ {slot} (wünschenswert)\n"
        
        rules += """
   
   Bei unklarer Antwort (Confidence < 0.8):
     → Rückfrage: "Verstehe ich richtig, dass Sie {interpretation}?"
     → Beispiel: "Sie sagten 'bald verfügbar' – meinen Sie innerhalb 
        der nächsten 4 Wochen oder eher 2-3 Monate?"

3. GATE-SEQUENZ (strikt einhalten!):
   
   ⚠️  Alle Gates MÜSSEN VOR Rahmenbedingungen geklärt sein!
   
   Reihenfolge:
     1. Gate: Qualifikation (muss erfüllt sein)
        → Bei Scheitern: Alternativen prüfen, dann ggf. Call beenden
     2. Gate: Verfügbarkeit (falls vorhanden)
        → Bei > 6 Monate: höflich beenden
   
   ✅ NUR wenn alle Gates bestanden → weiter zu Präferenzen

4. GESPRÄCHS-DIVERSITÄT:
   
   ❌ VERMEIDE:
     • 3+ Ja/Nein-Fragen hintereinander
     • Zu viele Choice-Fragen ohne Pausen
     • Starre Abarbeitung ohne Empathie
   
   ✅ MACHE:
     • Nach komplexer Frage → kurze Bestätigung: "Verstanden, danke!"
     • Nach Gate-Frage → Info einstreuen: "Super, dann erkläre ich 
       Ihnen kurz unsere Standorte..."
     • Zwischendurch Wertschätzung: "Das klingt nach wertvoller 
       Erfahrung!"

5. PROAKTIVE KLÄRUNG:
   
   Wenn Kandidat unsicher wirkt ("vielleicht", "weiß nicht", "kommt drauf an"):
     → Optionen konkretisieren
     → Beispiel: Statt nur "Teilzeit oder Vollzeit?" 
        besser: "Möchten Sie eher 50-75% arbeiten oder eine feste 
        3-Tage-Woche? Beides ist möglich."

6. EMPATHIE & TONALITÄT:
   
   • Bei negativer Gate-Antwort: "Vielen Dank für Ihre Offenheit..."
   • Bei Präferenzen: "Das verstehe ich gut..."
   • Bei Unsicherheit: "Kein Problem, wir können das später 
     konkretisieren..."
   • Bei guter Qualifikation: "Ausgezeichnet, das passt sehr gut!"

{'='*70}

"""
        return rules


