"""
Structure Pipeline Stage V2 - Generate-First, Filter-Later Approach

Neue Architektur:
1. GENERATE: Generiere ALLE Fragen ohne Filter
2. CLUSTER: Gruppiere ähnliche Fragen
3. CONSOLIDATE: Intelligente Zusammenführung
4. FILTER: Entferne nur wirklich unerwünschte Fragen

Vorteile:
- Keine Frage geht verloren
- Robuster gegen neue Kriterien-Typen
- Transparente Pipeline
- Gut testbar
"""

import logging
import re
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass

from ..types import (
    ExtractResult, 
    Question, 
    QuestionType, 
    QuestionGroup,
    ProtocolQuestion,
    GateConfig
)
from .structure import _extract_location_info  # Für Standort-Extraktion

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _slugify(text: str) -> str:
    """Create URL-safe slug from text"""
    text = text.lower()
    text = re.sub(r'[äöüß]', lambda m: {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss'}[m.group()], text)
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')


# Keywords für Fragetyp-Unterscheidung
BINARY_KEYWORDS = [
    'arbeitserlaubnis', 'aufenthaltserlaubnis',
    'impfung', 'impfnachweis', 'masern',
    'gesundheitszeugnis', 'einverstanden',
    'zustimmung', 'consent'
]

OPEN_KEYWORDS = [
    'ausbildung', 'qualifikation', 'abschluss',
    'studium', 'deutsch', 'sprach',
    'berufserfahrung', 'erfahrung', 'weiterbildung',
    'fortbildung', 'führerschein'
]

def _get_site_display_name(site) -> str:
    """
    Gibt den eleganten Display-Namen für einen Standort zurück.
    
    Verwendet primär das LLM-generierte display_name Feld.
    Fallback auf label wenn display_name nicht vorhanden.
    
    Args:
        site: Site-Objekt mit label und optional display_name
        
    Returns:
        Eleganter Stadtname für die Frage
    """
    # Primär: display_name vom LLM (falls vorhanden)
    display_name = getattr(site, 'display_name', None)
    if display_name and display_name.strip():
        return display_name.strip()
    
    # Fallback: label verwenden, aber versuchen Stadt zu extrahieren
    label = getattr(site, 'label', '') or ''
    
    if not label:
        return 'unbekannter Standort'
    
    # Simple Fallback: Stadt aus "PLZ Stadt" Pattern
    plz_city_match = re.search(r'\d{5}\s+([A-Za-zäöüÄÖÜß\-]+(?:\s+[A-Za-zäöüÄÖÜß\-]+)*)\s*$', label)
    if plz_city_match:
        return plz_city_match.group(1).strip()
    
    # Stadt in Klammern
    parens_match = re.search(r'\(([A-Za-zäöüÄÖÜß\-]+)\)\s*$', label)
    if parens_match:
        return parens_match.group(1)
    
    # Letzter Fallback: Label kürzen wenn zu lang
    if len(label) > 40:
        return label[:37] + "..."
    
    return label

# Preambles für systemische Gesprächsführung
GATE_PREAMBLES = {
    "qualifications": "Damit ich Ihren fachlichen Hintergrund einordnen kann:",
    "german_language": "Kurz zur Einordnung bezüglich der Sprachkenntnisse:",
    "experience": "Um Ihre Berufserfahrung besser zu verstehen:",
    "license": "Zum Thema Mobilität:",
    "health": "Eine kurze organisatorische Frage:"
}

PREFERENCE_PREAMBLES = {
    "location": "Was ist Ihnen bei der Wahl des Standorts wichtig:",
    "department": "Welcher Bereich kommt für Sie in Frage:",
    "working_hours": "Zum Thema Arbeitszeit:",
    "shifts": "Bezüglich der Schichtplanung:"
}


def _get_preamble(category: str, is_gate: bool = False) -> Optional[str]:
    """
    Gibt den passenden Preamble für eine Kategorie zurück.
    
    Args:
        category: Kategorie der Frage (z.B. "qualifications", "location")
        is_gate: Ob es eine Gate-Question ist
        
    Returns:
        Preamble-Text oder None
    """
    if is_gate:
        return GATE_PREAMBLES.get(category)
    else:
        return PREFERENCE_PREAMBLES.get(category)


def _formulate_question(text: str, is_gate: bool = False) -> str:
    """
    Formuliert aus einem Kriterium eine natürliche Frage.
    
    Logik:
    - Binäre Fakten (Ja/Nein) → Geschlossene Frage (BOOLEAN)
    - Mehrere Werte möglich → Offene Frage (STRING)
    
    Beispiele:
    - "Führerschein" → "Welchen Führerschein haben Sie?" (offen)
    - "Arbeitserlaubnis" → "Haben Sie eine gültige Arbeitserlaubnis?" (geschlossen)
    - "Deutsch B2" → "Wie würden Sie Ihre Deutschkenntnisse einschätzen?" (offen)
    """
    text_lower = text.lower()
    
    # Entferne Präfixe wie "zwingend:", "alternativ:", etc.
    text = re.sub(r'^(zwingend|alternativ|wünschenswert):\s*', '', text, flags=re.IGNORECASE).strip()
    text_lower = text.lower()
    
    # === OFFEN (STRING) - Mehrere Werte möglich ===
    
    # Führerschein (verschiedene Klassen)
    if 'führerschein' in text_lower:
        return "Welchen Führerschein haben Sie?"
    
    # Deutschkenntnisse (verschiedene Level)
    if 'deutsch' in text_lower:
        return "Wie würden Sie Ihre Deutschkenntnisse selbst einschätzen?"
    
    # Ausbildung/Qualifikation (verschiedene möglich)
    if any(kw in text_lower for kw in ['ausbildung', 'abschluss', 'studium']):
        # Spezielle Behandlung für "examiniert"
        if 'examinierte' in text_lower or 'examinierter' in text_lower:
            return f"Sind Sie {text.lower()}?"
        return "Welche Ausbildung haben Sie abgeschlossen?"
    
    # Qualifikation generisch
    if 'qualifikation' in text_lower:
        return "Welche Qualifikation haben Sie in diesem Bereich?"
    
    # Berufserfahrung (zeitlich variabel)
    if 'berufserfahrung' in text_lower or ('jahre' in text_lower and 'erfahrung' in text_lower):
        return "Wie lange arbeiten Sie schon in diesem Bereich?"
    
    # Weiterbildung (verschiedene möglich)
    if 'weiterbildung' in text_lower or 'fortbildung' in text_lower:
        return "Welche Weiterbildungen haben Sie absolviert?"
    
    # === GESCHLOSSEN (BOOLEAN) - Binäre Fakten ===
    
    # Arbeitserlaubnis (vorhanden oder nicht)
    if 'arbeitserlaubnis' in text_lower or 'aufenthaltserlaubnis' in text_lower:
        return "Haben Sie eine gültige Arbeitserlaubnis für Deutschland?"
    
    # Impfnachweise (vorhanden oder nicht)
    if 'impfung' in text_lower or 'impfnachweis' in text_lower or 'masern' in text_lower:
        return "Haben Sie die erforderlichen Impfnachweise?"
    
    # Gesundheitszeugnis (vorhanden oder nicht)
    if 'gesundheitszeugnis' in text_lower:
        return "Haben Sie ein gültiges Gesundheitszeugnis?"
    
    # Zustimmung/Consent (Ja/Nein)
    if any(kw in text_lower for kw in ['einverstanden', 'zustimmung', 'consent']):
        return f"Sind Sie einverstanden mit: {text}?"
    
    # === FALLBACK ===
    
    # Bei Gates: Offene Formulierung bevorzugen
    if is_gate:
        return f"Können Sie mir etwas zu folgendem Punkt sagen: {text}?"
    else:
        return f"Wie sieht Ihre Erfahrung mit {text} aus?"


def _detect_question_type(text: str) -> QuestionType:
    """
    Erkennt den Frage-Typ basierend auf dem Text.
    
    Logik:
    - BINARY Keywords → BOOLEAN
    - OPEN Keywords → STRING
    - Formulierung mit "Haben Sie", "Sind Sie" → BOOLEAN
    - Formulierung mit "Welche", "Wie" → STRING
    """
    text_lower = text.lower()
    
    # Binäre Keywords → BOOLEAN
    if any(kw in text_lower for kw in BINARY_KEYWORDS):
        return QuestionType.BOOLEAN
    
    # Offene Keywords → STRING
    if any(kw in text_lower for kw in OPEN_KEYWORDS):
        return QuestionType.STRING
    
    # Formulierung prüfen
    if any(kw in text_lower for kw in ['haben sie', 'sind sie', 'ist das', 'einverstanden']):
        return QuestionType.BOOLEAN
    
    if any(kw in text_lower for kw in ['welche', 'welcher', 'welches', 'wie würden', 'wie lange']):
        return QuestionType.STRING
    
    # Default: STRING (offene Frage)
    return QuestionType.STRING


def _is_name_or_address_question(text: str) -> bool:
    """Check if question is about name or address (should be filtered)"""
    text_lower = text.lower()
    
    # Name patterns
    if any(p in text_lower for p in [
        "spreche ich mit",
        "ist das herr",
        "ist das frau",
        "ihr name",
        "wie heißen sie"
    ]):
        return True
    
    # Address patterns  
    if any(p in text_lower for p in [
        "ich habe ihre adresse",
        "adresse als",
        "straße und hausnummer",
        "postleitzahl"
    ]):
        return True
    
    return False


def _detect_category(text: str, context: str = "") -> str:
    """
    Erkennt die Kategorie einer Frage für Clustering.
    
    Returns: Category-String (z.B. "qualifications", "arbeitszeit", "location")
    """
    combined = (text + " " + context).lower()
    
    # Qualifikationen
    if any(kw in combined for kw in [
        'ausbildung', 'abschluss', 'examen', 'studium', 'qualifikation',
        'fachkraft', 'weiterbildung', 'zertifikat', 'diplom'
    ]):
        return "qualifications"
    
    # Deutschkenntnisse (eigene Kategorie!)
    if any(kw in combined for kw in ['deutsch', 'sprachkenntnisse', 'b2', 'c1', 'muttersprachler']):
        return "german_language"
    
    # Führerschein
    if 'führerschein' in combined or 'fahrerlaubnis' in combined:
        return "driving_license"
    
    # Arbeitserlaubnis
    if 'arbeitserlaubnis' in combined or 'aufenthalt' in combined:
        return "work_permit"
    
    # Gesundheit/Impfungen
    if any(kw in combined for kw in ['impfung', 'impfnachweis', 'masern', 'gesundheit']):
        return "health"
    
    # Arbeitszeit
    if any(kw in combined for kw in [
        'vollzeit', 'teilzeit', 'stunden', 'wochenstunden', 'std', 'arbeitszeitmodell'
    ]):
        return "arbeitszeit"
    
    # Schichten
    if any(kw in combined for kw in [
        'nachtdienst', 'frühdienst', 'spätdienst', 'schicht', 'dienst', 'tagdienst'
    ]):
        return "schichten"
    
    # Gehalt
    if any(kw in combined for kw in ['gehalt', 'vergütung', 'tarif', 'lohn']):
        return "gehalt"
    
    # Benefits
    if any(kw in combined for kw in ['urlaub', 'benefit', 'prämie', 'vergünstigung']):
        return "benefits"
    
    # Standort
    if any(kw in combined for kw in ['standort', 'stadt', 'straße', 'ort']):
        return "location"
    
    # Abteilungen/Stationen
    if any(kw in combined for kw in ['abteilung', 'station', 'bereich', 'fachabteilung']):
        return "departments"
    
    # Berufserfahrung
    if any(kw in combined for kw in ['berufserfahrung', 'jahre erfahrung', 'erfahrung']):
        return "experience"
    
    # Unternehmenskultur
    if any(kw in combined for kw in ['du', 'sie', 'kommunikation', 'kultur', 'atmosphäre']):
        return "culture"
    
    # Soft Skills
    if any(kw in combined for kw in ['bereitschaft', 'flexibilität', 'teamfähigkeit']):
        return "soft_skills"
    
    # Default
    return "other"


def _extract_profession(text: str) -> Optional[str]:
    """
    Extrahiert die Berufsbezeichnung aus einem Qualifikations-Text.
    
    Beispiele:
    - "Abgeschlossene Ausbildung als Ergotherapeut" → "Ergotherapeut"
    - "Alternativ: Abgeschlossene Ausbildung als Physiotherapeut" → "Physiotherapeut"
    - "Examinierte Pflegefachkraft" → "Pflegefachkraft"
    """
    text = text.strip()
    
    # Entferne Präfixe
    prefixes_to_remove = [
        r'^alternativ:\s*', r'^zwingend:\s*', r'^optional:\s*',
        r'^abgeschlossene\s+ausbildung\s+als\s+', r'^abgeschlossenes?\s+studium\s+',
        r'^ausbildung\s+als\s+', r'^ausbildung\s+zum\s+', r'^ausbildung\s+zur\s+',
        r'^examinierte[r]?\s+', r'^staatlich\s+anerkannte[r]?\s+'
    ]
    
    cleaned = text
    for pattern in prefixes_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Nimm das erste signifikante Wort/Phrase
    cleaned = cleaned.strip()
    if cleaned:
        # Bis zum ersten Komma, Klammer oder "oder"
        match = re.match(r'^([^,(]+)', cleaned)
        if match:
            return match.group(1).strip()
    
    return None


def _group_qualifications_with_alternatives(
    must_haves: List[str], 
    alternatives: List[str]
) -> Tuple[List[Dict], List[str], List[str]]:
    """
    Gruppiert Ausbildungs-Must-Haves mit ihren Alternativen.
    
    Returns:
        (grouped_qualifications, remaining_must_haves, remaining_alternatives)
        
    grouped_qualifications: [{'main': 'Ergotherapeut', 'alternatives': ['Physiotherapeut'], 'original_must_have': '...'}]
    """
    grouped = []
    remaining_must_haves = []
    used_alternatives = set()
    
    for mh in must_haves:
        mh_lower = mh.lower()
        
        # Ist das eine Ausbildung/Qualifikation?
        if not any(kw in mh_lower for kw in ['ausbildung', 'abschluss', 'studium', 'examiniert']):
            remaining_must_haves.append(mh)
            continue
        
        # Extrahiere die Berufsbezeichnung
        main_profession = _extract_profession(mh)
        if not main_profession:
            remaining_must_haves.append(mh)
            continue
        
        # Suche passende Alternativen
        found_alternatives = []
        for i, alt in enumerate(alternatives):
            alt_lower = alt.lower()
            
            # Ist die Alternative auch eine Ausbildung?
            if any(kw in alt_lower for kw in ['ausbildung', 'abschluss', 'studium', 'examiniert']):
                alt_profession = _extract_profession(alt)
                if alt_profession and i not in used_alternatives:
                    found_alternatives.append(alt_profession)
                    used_alternatives.add(i)
        
        if found_alternatives:
            grouped.append({
                'main': main_profession,
                'alternatives': found_alternatives,
                'original_must_have': mh
            })
        else:
            # Keine Alternativen gefunden → als normale Frage
            remaining_must_haves.append(mh)
    
    # Verbleibende Alternativen
    remaining_alternatives = [
        alt for i, alt in enumerate(alternatives) 
        if i not in used_alternatives
    ]
    
    return grouped, remaining_must_haves, remaining_alternatives


# ============================================================================
# DATACLASSES FOR PIPELINE
# ============================================================================

@dataclass
class QuestionCluster:
    """Ein Cluster von ähnlichen Fragen"""
    category: str
    questions: List[Question]
    
    def __len__(self):
        return len(self.questions)
    
    @property
    def has_gates(self) -> bool:
        """Hat dieser Cluster Gate-Questions?"""
        return any(q.gate_config and q.gate_config.is_gate for q in self.questions)
    
    @property
    def gate_questions(self) -> List[Question]:
        """Nur Gate-Questions"""
        return [q for q in self.questions if q.gate_config and q.gate_config.is_gate]
    
    @property
    def preference_questions(self) -> List[Question]:
        """Nur Preference-Questions (keine Gates)"""
        return [q for q in self.questions if not (q.gate_config and q.gate_config.is_gate)]


# ============================================================================
# STAGE 1: GENERATE ALL QUESTIONS
# ============================================================================

def generate_all_questions(extract_result: ExtractResult) -> List[Question]:
    """
    Generiere für JEDES Item eine Frage, ohne Filter.
    Keine Frage geht verloren!
    
    Args:
        extract_result: Extrahierte Daten
        
    Returns:
        Liste ALLER generierten Fragen (ungefiltert)
    """
    questions = []
    question_id_counter = 1
    
    logger.info("🎯 Stage 1: GENERATE - Creating questions from all sources...")
    
    # ========================================
    # 0. NEU: Bevorzugte + Alternative Qualifikationen → EINE CHOICE-Frage
    # ========================================
    preferred = getattr(extract_result, 'preferred', []) or []
    alternatives = getattr(extract_result, 'alternatives', []) or []
    optional_quals = getattr(extract_result, 'optional_qualifications', []) or []
    
    # Wenn es bevorzugte oder alternative Qualifikationen gibt → CHOICE-Frage
    if preferred or alternatives:
        # Sammle alle Optionen
        all_options = []
        
        # Bevorzugte zuerst
        for pref in preferred:
            if pref and pref.strip():
                all_options.append(pref.strip())
        
        # Dann Alternativen
        for alt in alternatives:
            if alt and alt.strip() and alt.strip() not in all_options:
                all_options.append(alt.strip())
        
        # "Andere" Option am Ende
        if all_options:
            all_options.append("Andere")
            
            main_qual = all_options[0] if all_options else "Qualifikation"
            slug = _slugify(main_qual)
            preamble = GATE_PREAMBLES.get("qualifications", "Damit ich Ihren fachlichen Hintergrund einordnen kann:")
            
            questions.append(Question(
                id=f"qual_{slug}",
                question="Welche Ausbildung haben Sie abgeschlossen?",
                type=QuestionType.CHOICE,
                options=all_options,
                required=True,
                priority=1,
                group=QuestionGroup.QUALIFIKATION,
                context=f"Qualifikation: Bevorzugt {preferred}, Alternativen: {alternatives}",
                preamble=preamble,
                gate_config=GateConfig(
                    is_gate=True,
                    is_alternative=False,
                    has_alternatives=len(alternatives) > 0
                ),
                metadata={
                    "source_type": "unified_qualification",
                    "preferred": preferred,
                    "alternatives": alternatives,
                    "category": "qualifications"
                }
            ))
            question_id_counter += 1
            logger.info(f"  ✓ Einheitliche Qualifikations-Frage mit {len(all_options)} Optionen")
    
    # ========================================
    # 0b. NEU: Optionale Qualifikationen → Eigene Fragen mit Preamble
    # ========================================
    for opt_qual in optional_quals:
        if not opt_qual or not opt_qual.strip():
            continue
            
        slug = _slugify(opt_qual)
        
        # Spezielle Formulierung für optionale Items
        if 'führerschein' in opt_qual.lower():
            question_text = f"Haben Sie einen {opt_qual}?"
        else:
            question_text = f"Haben Sie {opt_qual}?"
        
        questions.append(Question(
            id=f"opt_{slug}",
            question=question_text,
            type=QuestionType.BOOLEAN,
            required=False,
            priority=3,  # Niedrigere Priorität
            group=QuestionGroup.PRAEFERENZEN,
            context=f"Optional: {opt_qual}",
            preamble="Das ist keine Voraussetzung, aber",  # NEUER PREAMBLE!
            gate_config=GateConfig(
                is_gate=False,
                is_alternative=False,
                has_alternatives=False
            ),
            metadata={
                "source_text": opt_qual,
                "source_type": "optional_qualification",
                "category": "optional"
            }
        ))
        question_id_counter += 1
        logger.info(f"  ✓ Optionale Frage: {opt_qual}")
    
    logger.info(f"  ✓ Generated qualification questions (preferred + alternatives + optional)")
    
    # ========================================
    # 1. Must-Haves (zwingende Anforderungen) → Gate Questions
    # ========================================
    must_have_count = 0
    for must_have in extract_result.must_have:
        # VALIDATION: Skip invalid items
        if not must_have or not must_have.strip():
            logger.warning(f"  ⚠️  Skipping empty must-have")
            continue
        
        slug = _slugify(must_have)
        if not slug:
            logger.warning(f"  ⚠️  Skipping must-have with invalid slug: {must_have[:50]}")
            continue
        
        question_text = _formulate_question(must_have, is_gate=True)
        if not question_text:
            logger.warning(f"  ⚠️  Failed to formulate question for: {must_have[:50]}")
            continue
        
        category = _detect_category(must_have, "must-have")
        preamble = _get_preamble(category, is_gate=True)
        
        questions.append(Question(
            id=f"mh_{slug}",
            question=question_text,
            type=QuestionType.STRING,  # Gates sind offen
            required=True,  # EXPLICIT
            priority=1,     # EXPLICIT
            group=QuestionGroup.QUALIFIKATION if category == "qualifications" else QuestionGroup.RAHMEN,
            context=f"Must-Have: {must_have}",
            preamble=preamble,
            gate_config=GateConfig(
                is_gate=True,
                is_alternative=False,
                has_alternatives=False
            ),
            metadata={"source_text": must_have, "source_type": "must_have", "category": category}
        ))
        question_id_counter += 1
        must_have_count += 1
    
    logger.info(f"  ✓ Generated {must_have_count} must-have gate questions")
    
    # ========================================
    # 2. ENTFERNT: Alternatives werden jetzt in der CHOICE-Frage behandelt
    # (siehe Schritt 0 oben)
    # ========================================
    logger.info(f"  ✓ Alternatives already included in CHOICE question")
    
    # ========================================
    # 3. Protocol Questions → direkt übernehmen
    # ========================================
    for pq in extract_result.protocol_questions:
        # Skip name/address questions
        if _is_name_or_address_question(pq.text):
            continue
        
        # Robuste Type-Konvertierung (LLM kann ungültige Types wie "information" zurückgeben)
        try:
            q_type = QuestionType(pq.type) if pq.type else _detect_question_type(pq.text)
        except ValueError:
            logger.warning(f"  Invalid question type '{pq.type}' for question: {pq.text[:50]}... Using STRING")
            q_type = QuestionType.STRING
        category = _detect_category(pq.text, pq.category or "")
        
        questions.append(Question(
            id=f"pq_{pq.page_id}_{pq.prompt_id or question_id_counter}",
            question=pq.text,
            type=q_type,
            options=pq.options,
            required=pq.is_required,
            priority=1 if pq.is_gate else 2,
            group=QuestionGroup.QUALIFIKATION if "qualif" in (pq.category or "") else QuestionGroup.PRAEFERENZEN,
            context=f"Protocol Question (Page {pq.page_id})",
            gate_config=GateConfig(is_gate=True) if pq.is_gate else None,
            metadata={"source_text": pq.text, "source_type": "protocol_question", "category": category}
        ))
        question_id_counter += 1
    
    logger.info(f"  ✓ Generated {len(extract_result.protocol_questions)} questions from protocol")
    
    # ========================================
    # 4. Constraints → Fragen generieren
    # ========================================
    
    # 4a. Arbeitszeit - NEU: Unterscheidung Zwingend vs. Optional
    if extract_result.constraints and extract_result.constraints.arbeitszeit:
        az = extract_result.constraints.arbeitszeit
        az_str = str(az) if az else ""
        az_lower = az_str.lower()
        
        # Prüfe ob "zwingend" markiert (z.B. "Zwingend: Vollzeit 39,5 Stunden")
        is_mandatory = any(kw in az_lower for kw in ['zwingend', 'erforderlich', 'muss', 'pflicht'])
        
        # Extrahiere die eigentliche Arbeitszeit-Info (ohne "Zwingend:")
        arbeitszeit_info = re.sub(r'^zwingend\s*:\s*', '', az_str, flags=re.IGNORECASE).strip()
        
        if is_mandatory:
            # ZWINGEND: Gate-Frage mit speziellem Preamble
            # "Die Stelle ist für Vollzeit 39,5 Stunden die Woche ausgeschrieben"
            preamble = f"Die Stelle ist für {arbeitszeit_info} ausgeschrieben."
            
            questions.append(Question(
                id="constraint_arbeitszeit_mandatory",
                question="Passt das für Sie?",
                type=QuestionType.BOOLEAN,
                required=True,
                priority=1,  # Höhere Priorität bei zwingend
                group=QuestionGroup.RAHMEN,
                context=f"Zwingende Arbeitszeit: {arbeitszeit_info}",
                preamble=preamble,
                gate_config=GateConfig(
                    is_gate=True,  # Gate bei zwingend!
                    is_alternative=False,
                    has_alternatives=False
                ),
                metadata={
                    "source_text": az_str, 
                    "source_type": "constraint_mandatory", 
                    "category": "arbeitszeit",
                    "is_mandatory": True
                }
            ))
            question_id_counter += 1
            logger.info(f"  ✓ Zwingende Arbeitszeit-Frage: {arbeitszeit_info}")
        else:
            # OPTIONAL: Auswahl-Frage wie bisher
            working_hours_preamble = "Ich möchte kurz auf das Arbeitszeitmodell eingehen."
            
            # Wenn es ein Arbeitszeit-Objekt ist
            if isinstance(az, dict) or hasattr(az, 'vollzeit'):
                az_obj = az if isinstance(az, dict) else az.model_dump() if hasattr(az, 'model_dump') else {}
                vollzeit = az_obj.get('vollzeit', '')
                teilzeit = az_obj.get('teilzeit', '')
                
                # Baue Preamble mit Details
                detail_parts = []
                if vollzeit:
                    detail_parts.append(f"Vollzeit={vollzeit}")
                if teilzeit:
                    detail_parts.append(f"Teilzeit={teilzeit}")
                
                if detail_parts:
                    working_hours_preamble += f" {'. '.join(detail_parts)}."
                
                questions.append(Question(
                    id="constraint_arbeitszeit",
                    question="Haben Sie eine Präferenz bezüglich des Arbeitszeitmodells?",
                    type=QuestionType.CHOICE,
                    options=["Vollzeit", "Teilzeit", "Bin flexibel"],
                    required=True,
                    priority=2,
                    group=QuestionGroup.RAHMEN,
                    context="Arbeitszeitmodell aus Constraints",
                    preamble=working_hours_preamble,
                    metadata={"source_text": str(az), "source_type": "constraint", "category": "arbeitszeit"}
                ))
                question_id_counter += 1
            # Wenn es ein einfacher String ist
            elif isinstance(az, str) and arbeitszeit_info:
                questions.append(Question(
                    id="constraint_arbeitszeit_str",
                    question=f"Die ausgeschriebene Arbeitszeit ist {arbeitszeit_info}. Passt das für Sie?",
                    type=QuestionType.BOOLEAN,
                    required=True,
                    priority=2,
                    group=QuestionGroup.RAHMEN,
                    context=f"Arbeitszeit: {arbeitszeit_info}",
                    preamble=working_hours_preamble,
                    metadata={"source_text": az_str, "source_type": "constraint", "category": "arbeitszeit"}
                ))
                question_id_counter += 1
    
    # 4b. Gehalt
    if extract_result.constraints and extract_result.constraints.gehalt:
        gehalt_info = extract_result.constraints.gehalt
        gehalt_text = gehalt_info if isinstance(gehalt_info, str) else gehalt_info.get('betrag', '')
        
        if gehalt_text:
            questions.append(Question(
                id="constraint_gehalt",
                question=f"Unser Gehaltsrahmen liegt bei {gehalt_text}. Passt das für Sie?",
                type=QuestionType.BOOLEAN,
                required=False,
                priority=2,
                group=QuestionGroup.RAHMEN,
                context=f"Gehalt: {gehalt_text}",
                metadata={"source_text": gehalt_text, "source_type": "constraint", "category": "gehalt"}
            ))
            question_id_counter += 1
    
    # 4c. Schichten
    if extract_result.constraints and extract_result.constraints.schichten:
        shifts_preamble = _get_preamble("shifts", is_gate=False)
        
        questions.append(Question(
            id="constraint_schichten",
            question="Sind Sie bereit, im Schichtdienst zu arbeiten?",
            type=QuestionType.BOOLEAN,
            required=False,
            priority=2,
            group=QuestionGroup.RAHMEN,
            context=f"Schichtdienst: {extract_result.constraints.schichten}",
            preamble=shifts_preamble,
            metadata={"source_text": extract_result.constraints.schichten, "source_type": "constraint", "category": "schichten"}
        ))
        question_id_counter += 1
    
    logger.info(f"  ✓ Generated questions from constraints")
    
    # ========================================
    # 5. Standorte → Frage generieren (mit LLM-basierter Stadt-Extraktion)
    # ========================================
    if extract_result.sites and len(extract_result.sites) > 0:
        location_preamble = _get_preamble("location", is_gate=False)
        
        # Extrahiere Location-Infos für alle Sites
        locations = []
        for site in extract_result.sites:
            # Nutze address falls vorhanden, sonst label
            address_to_parse = getattr(site, 'address', None) or site.label or ''
            loc_info = _extract_location_info(address_to_parse)
            # Region aus site.region_context oder extrahiertem district
            region = getattr(site, 'region_context', None) or loc_info.get('district')
            loc_info['region'] = region
            loc_info['einrichtung'] = site.label  # Einrichtungsname separat speichern
            locations.append(loc_info)
        
        # Prüfe ob es region_context auf extract_result-Ebene gibt
        global_region = getattr(extract_result, 'region_context', None)
        
        # Extrahiere Stadtteil aus global_region falls vorhanden (z.B. "Region Marzahn Hellersdorf" -> "Marzahn-Hellersdorf")
        if global_region:
            global_region = global_region.replace("Region ", "").replace(" ", "-").strip()
        
        # Einfache Standort-Frage generieren
        if len(extract_result.sites) == 1:
            site = extract_result.sites[0]
            loc = locations[0]
            
            # Extrahiere Stadt aus Adresse - suche nach bekannten Stadtmustern
            city = loc.get('city', '')
            
            # Fix: Wenn city die volle Adresse enthält, extrahiere nur den Stadtnamen
            # Suche nach PLZ-Stadt Muster (z.B. "12627 Berlin")
            if city:
                plz_city_match = re.search(r'\d{5}\s+([A-ZÄÖÜa-zäöü\-]+)', city)
                if plz_city_match:
                    city = plz_city_match.group(1)
                # Fallback: Suche nach bekannten Stadtnamen
                elif 'Berlin' in city:
                    city = 'Berlin'
                elif 'München' in city:
                    city = 'München'
                elif 'Hamburg' in city:
                    city = 'Hamburg'
            
            # Bestimme den besten Standort-Text für die Frage
            # Priorität: Stadt + Region > Stadt + Stadtteil > nur Stadt > Einrichtungsname
            region = global_region or loc.get('region') or loc.get('district')
            
            if city and region:
                location_text = f"{city} {region}"
            elif city:
                location_text = city
            elif region:
                location_text = region
            else:
                # Fallback auf Einrichtungsname
                location_text = site.label or 'unbekannter Standort'
            
            # Volle Adresse für Kontext (Einrichtung + Adresse)
            einrichtung = loc.get('einrichtung', site.label)
            full_address = getattr(site, 'address', None) or loc.get('full_address', site.label)
            context_text = f"{einrichtung}, {full_address}" if einrichtung != full_address else full_address
            
            questions.append(Question(
                id="site_single",
                question=f"Unser Standort ist in {location_text}. Passt das für Sie?",
                type=QuestionType.BOOLEAN,
                required=True,
                priority=1,
                group=QuestionGroup.STANDORT,
                context=f"Vollständige Adresse: {context_text}",
                preamble=location_preamble,
                metadata={"source_text": context_text, "source_type": "site", "category": "location"}
            ))
            logger.info(f"  ✓ Site: '{site.label}' → Location: '{location_text}'")
        else:
            # Mehrere Standorte - nutze Städte oder Straßen als Optionen
            cities = set(loc.get('city') for loc in locations if loc.get('city'))
            
            if len(cities) == 1:
                # Alle in derselben Stadt → Straßen als Optionen
                site_options = [loc.get('street') or extract_result.sites[i].label 
                               for i, loc in enumerate(locations)]
                city_name = list(cities)[0]
                preamble = f"Wir haben mehrere Standorte in {city_name}. Haben Sie eine Präferenz?"
            else:
                # Verschiedene Städte → Städte als Optionen
                site_options = [loc.get('city') or extract_result.sites[i].label 
                               for i, loc in enumerate(locations)]
                preamble = None
            
            questions.append(Question(
                id="site_multiple",
                question="Haben Sie bereits eine Präferenz für einen bestimmten Standort?",
                type=QuestionType.CHOICE,
                options=site_options,
                required=True,
                priority=1,
                group=QuestionGroup.STANDORT,
                context=f"{len(site_options)} Standorte verfügbar",
                preamble=preamble or location_preamble,
                metadata={"source_text": ', '.join(site_options), "source_type": "site", "category": "location"}
            ))
            logger.info(f"  ✓ Sites: {len(site_options)} locations")
        question_id_counter += 1
    
    logger.info(f"  ✓ Generated location questions")
    
    # ========================================
    # 6. Abteilungen → Frage generieren
    # ========================================
    if extract_result.all_departments and len(extract_result.all_departments) > 1:
        department_preamble = _get_preamble("department", is_gate=False)
        
        questions.append(Question(
            id="departments",
            question="In welchem Bereich möchten Sie gerne arbeiten?",
            type=QuestionType.CHOICE,
            options=extract_result.all_departments,
            required=False,
            priority=2,
            group=QuestionGroup.EINSATZBEREICH,
            context=f"{len(extract_result.all_departments)} Abteilungen verfügbar",
            preamble=department_preamble,
            metadata={"source_text": ', '.join(extract_result.all_departments), "source_type": "departments", "category": "departments"}
        ))
        question_id_counter += 1
    
    logger.info(f"  ✓ Generated department questions")
    
    total = len(questions)
    logger.info(f"✅ Stage 1 complete: {total} questions generated (ungefiltert)")
    
    return questions


# ============================================================================
# STAGE 2: CLUSTER QUESTIONS
# ============================================================================

def cluster_questions(questions: List[Question]) -> List[QuestionCluster]:
    """
    Gruppiere ähnliche Fragen in Cluster basierend auf Kategorie.
    
    Args:
        questions: Alle generierten Fragen
        
    Returns:
        Liste von QuestionCluster-Objekten
    """
    logger.info("🎯 Stage 2: CLUSTER - Grouping similar questions...")
    
    # Dictionary: category → List[Question]
    clusters_dict: Dict[str, List[Question]] = {}
    
    for q in questions:
        # Hole Kategorie aus metadata
        category = q.metadata.get('category', 'other') if q.metadata else 'other'
        
        if category not in clusters_dict:
            clusters_dict[category] = []
        
        clusters_dict[category].append(q)
    
    # Konvertiere zu QuestionCluster-Objekten
    clusters = [
        QuestionCluster(category=cat, questions=questions_list)
        for cat, questions_list in clusters_dict.items()
    ]
    
    # Sortiere Cluster nach Priorität (Gates zuerst)
    clusters.sort(key=lambda c: (not c.has_gates, c.category))
    
    # Log Cluster-Statistik
    for cluster in clusters:
        gate_count = len(cluster.gate_questions)
        pref_count = len(cluster.preference_questions)
        logger.info(f"  📦 {cluster.category}: {len(cluster)} questions ({gate_count} gates, {pref_count} prefs)")
    
    logger.info(f"✅ Stage 2 complete: {len(clusters)} clusters created")
    
    return clusters


# ============================================================================
# STAGE 3: CONSOLIDATE CLUSTERS
# ============================================================================

def consolidate_clusters(clusters: List[QuestionCluster]) -> List[Question]:
    """
    Intelligente Zusammenführung von Fragen innerhalb jedes Clusters.
    
    Regeln:
    1. Einzelne Frage → behalten
    2. Mehrere Gates → NICHT konsolidieren (jedes separat)
    3. Mix aus Gates + Preferences → Gates separat, Preferences ggf. konsolidieren
    4. Arbeitszeit/Schicht-Fragmente → konsolidieren
    5. Duplikate → nur eine behalten
    
    Args:
        clusters: Liste von Frage-Clustern
        
    Returns:
        Konsolidierte Liste von Fragen
    """
    logger.info("🎯 Stage 3: CONSOLIDATE - Merging questions intelligently...")
    
    consolidated = []
    
    for cluster in clusters:
        logger.debug(f"  Processing cluster: {cluster.category} ({len(cluster)} questions)")
        
        # Regel 1: Einzelne Frage → behalten
        if len(cluster) == 1:
            consolidated.append(cluster.questions[0])
            logger.debug(f"    ✓ Single question - keeping as-is")
            continue
        
        # Regel 2: Nur Gates → ALLE separat behalten
        if cluster.has_gates and len(cluster.preference_questions) == 0:
            logger.info(f"    ✓ {len(cluster.gate_questions)} gate questions - keeping all separate")
            consolidated.extend(cluster.gate_questions)
            continue
        
        # Regel 3: Mix aus Gates + Preferences
        if cluster.has_gates and len(cluster.preference_questions) > 0:
            # Gates separat
            consolidated.extend(cluster.gate_questions)
            logger.info(f"    ✓ {len(cluster.gate_questions)} gates kept separate")
            
            # Preferences: Entferne Duplikate und konsolidiere falls sinnvoll
            prefs = _deduplicate_questions(cluster.preference_questions)
            
            if cluster.category == "qualifications" and len(prefs) >= 2:
                # Konsolidiere Qualifikations-Preferences zu Multi-Choice
                merged = _merge_to_multichoice(prefs, cluster.category)
                consolidated.append(merged)
                logger.info(f"    ✓ Merged {len(prefs)} preferences into multi-choice")
            else:
                consolidated.extend(prefs)
                logger.info(f"    ✓ {len(prefs)} preferences kept separate")
            continue
        
        # Regel 4: Arbeitszeit/Schicht-Fragmente konsolidieren
        if cluster.category in ["arbeitszeit", "schichten"]:
            if _are_fragments(cluster.questions):
                merged = _consolidate_arbeitszeit_schicht(cluster)
                if merged:
                    consolidated.append(merged)
                    logger.info(f"    ✓ Consolidated {len(cluster)} fragments into single question")
                    continue
        
        # Regel 5: Deduplizierung
        deduped = _deduplicate_questions(cluster.questions)
        consolidated.extend(deduped)
        logger.info(f"    ✓ Deduplicated: {len(cluster)} → {len(deduped)} questions")
    
    logger.info(f"✅ Stage 3 complete: {len(consolidated)} questions after consolidation")
    
    return consolidated


def _deduplicate_questions(questions: List[Question]) -> List[Question]:
    """Entferne Duplikate basierend auf Frage-Text"""
    seen_texts = set()
    unique = []
    
    for q in questions:
        q_text_normalized = q.question.lower().strip()
        if q_text_normalized not in seen_texts:
            seen_texts.add(q_text_normalized)
            unique.append(q)
        else:
            logger.debug(f"      Removed duplicate: {q.question[:50]}")
    
    return unique


def _are_fragments(questions: List[Question]) -> bool:
    """Prüft ob Fragen Fragmente sind (keine vollständigen Fragen)"""
    # Fragmente haben oft:
    # - Keinen "?" am Ende
    # - Kein Fragewort
    # - Kurze Texte
    
    fragment_count = 0
    for q in questions:
        text = q.question
        if '?' not in text or len(text) < 20:
            fragment_count += 1
    
    # Wenn mehr als die Hälfte Fragmente sind
    return fragment_count >= len(questions) / 2


def _consolidate_arbeitszeit_schicht(cluster: QuestionCluster) -> Optional[Question]:
    """Konsolidiert Arbeitszeit/Schicht-Fragmente zu einer Frage"""
    
    if cluster.category == "arbeitszeit":
        # Sammle Details
        details = []
        for q in cluster.questions:
            source_text = q.metadata.get('source_text', '') if q.metadata else ''
            if source_text:
                details.append(source_text)
        
        if details:
            preamble = "Ich möchte kurz auf das Arbeitszeitmodell eingehen. " + ". ".join(details) + "."
            return Question(
                id="arbeitszeit_consolidated",
                preamble=preamble,
                question="Haben Sie eine Präferenz bezüglich des Arbeitszeitmodells?",
                type=QuestionType.CHOICE,
                options=["Vollzeit", "Teilzeit", "Bin flexibel"],
                required=True,
                priority=2,
                group=QuestionGroup.RAHMEN,
                context="Konsolidierte Arbeitszeit-Frage",
                metadata={"category": "arbeitszeit", "source_type": "consolidated"}
            )
    
    elif cluster.category == "schichten":
        # Sammle Schicht-Details
        schichten = []
        for q in cluster.questions:
            source_text = q.metadata.get('source_text', '') if q.metadata else ''
            if source_text:
                schichten.append(source_text)
        
        if schichten:
            return Question(
                id="schichten_consolidated",
                preamble="Wir arbeiten in verschiedenen Schichtmodellen.",
                question="Welche Schichtmodelle kommen für Sie in Frage? Sie können auch mehrere nennen.",
                type=QuestionType.MULTI_CHOICE,
                options=schichten,
                required=False,
                priority=2,
                group=QuestionGroup.RAHMEN,
                context="Konsolidierte Schicht-Frage",
                metadata={"category": "schichten", "source_type": "consolidated"}
            )
    
    return None


def _merge_to_multichoice(questions: List[Question], category: str) -> Question:
    """Merged mehrere ähnliche Fragen zu einer Multi-Choice Frage"""
    
    # Sammle alle Options/Texte
    options = []
    for q in questions:
        source_text = q.metadata.get('source_text', '') if q.metadata else ''
        if source_text:
            # Entferne Präfixe
            source_text = re.sub(r'^(zwingend|alternativ|wünschenswert):\s*', '', source_text, flags=re.IGNORECASE).strip()
            options.append(source_text)
    
    # Dedupliziere
    options = list(dict.fromkeys(options))  # Preserve order
    
    # Generiere Frage-Text
    if category == "qualifications":
        question_text = "Welche der folgenden Qualifikationen haben Sie?"
        preamble = "Ich würde gerne Ihre Qualifikation abklären." if len(options) > 3 else None
    else:
        question_text = f"Welche der folgenden Optionen trifft auf Sie zu?"
        preamble = None
    
    return Question(
        id=f"{category}_consolidated_multichoice",
        question=question_text,
        preamble=preamble,
        type=QuestionType.MULTI_CHOICE,
        options=options,
        required=False,
        priority=2,
        group=QuestionGroup.QUALIFIKATION if category == "qualifications" else QuestionGroup.PRAEFERENZEN,
        context=f"Konsolidierte Multi-Choice aus {len(questions)} Fragen",
        metadata={"category": category, "source_type": "consolidated_multichoice"}
    )


# ============================================================================
# STAGE 4: FILTER QUESTIONS
# ============================================================================

def filter_questions(questions: List[Question]) -> List[Question]:
    """
    Entferne nur wirklich unerwünschte Fragen.
    
    Filter-Regeln:
    1. Name/Adresse-Fragen
    2. Exakte Duplikate (identischer Text)
    3. Zu generische Fragen ohne Kontext
    4. NEU: Kategorie-Deduplizierung (nur eine Standort-Frage, etc.)
    5. NEU: Informationen statt Fragen (z.B. "Standort: X" ohne Fragezeichen)
    
    Args:
        questions: Konsolidierte Fragen
        
    Returns:
        Gefilterte Liste von Fragen
    """
    logger.info("🎯 Stage 4: FILTER - Removing unwanted questions...")
    
    filtered = []
    seen_texts = set()
    seen_categories = {}  # NEU: Tracke bereits gesehene Kategorien
    
    # Kategorien die nur einmal vorkommen sollten
    SINGLE_CATEGORY_TYPES = {'location', 'departments', 'arbeitszeit', 'gehalt'}
    
    for q in questions:
        # Filter 1: Name/Adresse
        if _is_name_or_address_question(q.question):
            logger.debug(f"  🗑️  Filtered (name/address): {q.question[:50]}")
            continue
        
        # Filter 2: Exakte Duplikate
        q_normalized = q.question.lower().strip()
        if q_normalized in seen_texts:
            logger.debug(f"  🗑️  Filtered (duplicate): {q.question[:50]}")
            continue
        
        # Filter 3: Zu generisch
        if len(q.question) < 10 and not q.context:
            logger.debug(f"  🗑️  Filtered (too generic): {q.question[:50]}")
            continue
        
        # Filter 4: NEU - Informationen statt Fragen (kein Fragezeichen, keine echte Frage)
        if not q.question.endswith('?') and not any(kw in q.question.lower() for kw in 
            ['haben sie', 'können sie', 'möchten sie', 'passt', 'welche', 'wie', 'sind sie']):
            # Prüfe ob es eine Information ist (z.B. "Standort: X")
            if ':' in q.question and len(q.question.split(':')) == 2:
                logger.debug(f"  🗑️  Filtered (info not question): {q.question[:50]}")
                continue
        
        # Filter 5: NEU - Kategorie-Deduplizierung
        category = q.metadata.get('category', '') if q.metadata else ''
        if category in SINGLE_CATEGORY_TYPES:
            if category in seen_categories:
                # Behalte die Frage mit höherer Priorität (niedrigere Zahl = höher)
                existing_q = seen_categories[category]
                if q.priority < existing_q.priority:
                    # Diese Frage hat höhere Priorität → ersetze
                    filtered.remove(existing_q)
                    seen_categories[category] = q
                    filtered.append(q)
                    logger.debug(f"  🔄 Replaced lower-priority {category} question")
                else:
                    logger.debug(f"  🗑️  Filtered (duplicate category {category}): {q.question[:50]}")
                continue
            seen_categories[category] = q
        
        # Behalten!
        filtered.append(q)
        seen_texts.add(q_normalized)
    
    removed_count = len(questions) - len(filtered)
    logger.info(f"✅ Stage 4 complete: {len(filtered)} questions (removed {removed_count})")
    
    return filtered


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def build_questions_v2(extract_result: ExtractResult, classified_data: Dict = None) -> List[Question]:
    """
    Hauptfunktion: Neue 4-Stage Pipeline (V1-kompatibel)
    
    Stage 1: GENERATE - Alle Fragen generieren
    Stage 2: CLUSTER - Ähnliche Fragen gruppieren  
    Stage 3: CONSOLIDATE - Intelligente Zusammenführung
    Stage 4: FILTER - Unerwünschte entfernen
    
    Args:
        extract_result: Extrahierte Daten aus dem Protokoll
        classified_data: Optional - Klassifizierte Protokoll-Items (from STAGE 0)
        
    Returns:
        List[Question]: Liste von finalen Fragen (SAME as V1)
        
    Note:
        Knowledge-Base wird separat in extract_result.metadata gespeichert
    """
    # #region agent log
    import json, time
    with open(r'c:\Users\David Jekal\Desktop\Projekte\KI-Sellcrtuiting_VoiceKI\.cursor\debug.log', 'a') as f: f.write(json.dumps({'location':'structure_v2.py:773','message':'V2 Entry','data':{'must_haves':len(extract_result.must_have),'alternatives':len(extract_result.alternatives),'protocol_questions':len(extract_result.protocol_questions)},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'E'})+'\n')
    # #endregion
    
    # #region agent log
    import json, time
    with open(r'c:\Users\David Jekal\Desktop\Projekte\KI-Sellcrtuiting_VoiceKI\.cursor\debug.log', 'a') as f: f.write(json.dumps({'location':'structure_v2.py:800','message':'V2 Entry','data':{'must_haves':len(extract_result.must_have),'alternatives':len(extract_result.alternatives),'sites':len(extract_result.sites),'has_classified_data':classified_data is not None},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'C'})+'\n')
    # #endregion
    
    logger.info("=" * 70)
    logger.info("🚀 Starting Question Builder V2 (Generate-First, Filter-Later)")
    logger.info("=" * 70)
    
    # Stage 1: Generate ALL
    all_questions = generate_all_questions(extract_result)
    
    # #region agent log
    with open(r'c:\Users\David Jekal\Desktop\Projekte\KI-Sellcrtuiting_VoiceKI\.cursor\debug.log', 'a') as f: f.write(json.dumps({'location':'structure_v2.py:812','message':'After Generate Stage','data':{'generated_count':len(all_questions)},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'C'})+'\n')
    # #endregion
    
    # #region agent log
    with open(r'c:\Users\David Jekal\Desktop\Projekte\KI-Sellcrtuiting_VoiceKI\.cursor\debug.log', 'a') as f: f.write(json.dumps({'location':'structure_v2.py:806','message':'After GENERATE','data':{'count':len(all_questions),'has_metadata':all_questions[0].metadata is not None if all_questions else False},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'E'})+'\n')
    # #endregion
    
    # Stage 2: Cluster
    clusters = cluster_questions(all_questions)
    
    # Stage 3: Consolidate
    consolidated = consolidate_clusters(clusters)
    
    # Stage 4: Filter
    filtered = filter_questions(consolidated)
    
    # #region agent log - VALIDATION CHECK (Hypothese F)
    validation_results = []
    for idx, q in enumerate(filtered[:3]):  # Check first 3 questions
        try:
            # Check all required fields
            validation = {
                'idx': idx,
                'id': q.id,
                'question': q.question[:50] if q.question else None,
                'type': str(q.type),
                'required': q.required,
                'priority': q.priority,
                'group': str(q.group) if q.group else None,
                'has_metadata': q.metadata is not None,
                'has_gate_config': q.gate_config is not None,
                'valid': True
            }
            # Try model_dump to see if it works
            try:
                q.model_dump()
                validation['model_dump_ok'] = True
            except Exception as e:
                validation['model_dump_ok'] = False
                validation['model_dump_error'] = str(e)
        except Exception as e:
            validation = {'idx': idx, 'valid': False, 'error': str(e)}
        validation_results.append(validation)
    
    with open(r'c:\Users\David Jekal\Desktop\Projekte\KI-Sellcrtuiting_VoiceKI\.cursor\debug.log', 'a') as f: f.write(json.dumps({'location':'structure_v2.py:820','message':'V2 Exit with Validation','data':{'count':len(filtered),'validation_results':validation_results},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'A,B,C,D,F'})+'\n')
    # #endregion
    
    logger.info("=" * 70)
    logger.info(f"✅ Pipeline complete: {len(filtered)} final questions")
    logger.info("=" * 70)
    
    # Stage 5: Build Knowledge-Base (stored in extract_result for later access)
    if classified_data:
        try:
            from .knowledge_base import build_knowledge_base
            knowledge_base = build_knowledge_base(
                information_items=classified_data.get('information_items', []),
                constraints=extract_result.constraints,
                priority_items=classified_data.get('priorities', []),
                internal_note_items=classified_data.get('internal_notes', []),
                metadata_items=classified_data.get('metadata', []),
                # NEU: Kultur-Notizen und AP-Zuordnung aus Extractor
                culture_notes=getattr(extract_result, 'culture_notes', []) or [],
                department_contacts=getattr(extract_result, 'department_contacts', {}) or {}
            )
            # Store KB in extract_result for later retrieval
            if not hasattr(extract_result, '_knowledge_base'):
                object.__setattr__(extract_result, '_knowledge_base', knowledge_base)
        except Exception as e:
            logger.error(f"Failed to build knowledge base: {e}")
    
    # #region agent log
    with open(r'c:\Users\David Jekal\Desktop\Projekte\KI-Sellcrtuiting_VoiceKI\.cursor\debug.log', 'a') as f: f.write(json.dumps({'location':'structure_v2.py:873','message':'V2 Exit','data':{'final_count':len(filtered),'return_type':str(type(filtered))},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'C'})+'\n')
    # #endregion
    
    # Return ONLY questions list (same as V1)
    return filtered

