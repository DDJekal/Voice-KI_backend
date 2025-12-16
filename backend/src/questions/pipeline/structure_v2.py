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
    # 1. Must-Haves → Gate Questions
    # ========================================
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
    
    logger.info(f"  ✓ Generated {len(extract_result.must_have)} questions from must-haves")
    
    # ========================================
    # 2. Alternatives → Preference Questions
    # ========================================
    for alt in extract_result.alternatives:
        # VALIDATION: Skip invalid items
        if not alt or not alt.strip():
            logger.warning(f"  ⚠️  Skipping empty alternative")
            continue
        
        slug = _slugify(alt)
        if not slug:
            logger.warning(f"  ⚠️  Skipping alternative with invalid slug: {alt[:50]}")
            continue
        
        question_text = _formulate_question(alt, is_gate=False)
        if not question_text:
            logger.warning(f"  ⚠️  Failed to formulate question for: {alt[:50]}")
            continue
        
        category = _detect_category(alt, "alternative")
        
        questions.append(Question(
            id=f"alt_{slug}",
            question=question_text,
            type=QuestionType.BOOLEAN,  # Alternatives als Boolean
            required=False,  # EXPLICIT
            priority=2,      # EXPLICIT
            group=QuestionGroup.QUALIFIKATION if category == "qualifications" else QuestionGroup.PRAEFERENZEN,
            context=f"Alternative: {alt}",
            metadata={"source_text": alt, "source_type": "alternative", "category": category}
        ))
        question_id_counter += 1
    
    logger.info(f"  ✓ Generated {len(extract_result.alternatives)} questions from alternatives")
    
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
    
    # 4a. Arbeitszeit
    if extract_result.constraints and extract_result.constraints.arbeitszeit:
        az = extract_result.constraints.arbeitszeit
        working_hours_preamble = _get_preamble("working_hours", is_gate=False)
        
        # Wenn es ein Arbeitszeit-Objekt ist
        if isinstance(az, dict) or hasattr(az, 'vollzeit'):
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
        # Wenn es ein String ist (z.B. "38-40 Wochenstunden")
        elif isinstance(az, str):
            questions.append(Question(
                id="constraint_arbeitszeit_str",
                question=f"Die Stelle ist in {az}. Passt das für Sie?",
                type=QuestionType.BOOLEAN,
                required=True,
                priority=2,
                group=QuestionGroup.RAHMEN,
                context=f"Arbeitszeit: {az}",
                preamble=working_hours_preamble,
                metadata={"source_text": az, "source_type": "constraint", "category": "arbeitszeit"}
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
    # 5. Standorte → Frage generieren
    # ========================================
    if extract_result.sites and len(extract_result.sites) > 0:
        location_preamble = _get_preamble("location", is_gate=False)
        
        # Einfache Standort-Frage generieren
        if len(extract_result.sites) == 1:
            site = extract_result.sites[0]
            site_name = site.label or 'unbekannter Standort'
            questions.append(Question(
                id="site_single",
                question=f"Unser Standort ist in {site_name}. Passt das für Sie?",
                type=QuestionType.BOOLEAN,
                required=True,
                priority=1,
                group=QuestionGroup.STANDORT,
                context=f"Standort: {site_name}",
                preamble=location_preamble,
                metadata={"source_text": site_name, "source_type": "site", "category": "location"}
            ))
        else:
            # Mehrere Standorte
            site_names = [s.label or f"Standort {i+1}" 
                         for i, s in enumerate(extract_result.sites)]
            questions.append(Question(
                id="site_multiple",
                question="Haben Sie bereits eine Präferenz für einen bestimmten Standort?",
                type=QuestionType.CHOICE,
                options=site_names,
                required=True,
                priority=1,
                group=QuestionGroup.STANDORT,
                context=f"{len(site_names)} Standorte verfügbar",
                preamble=location_preamble,
                metadata={"source_text": ', '.join(site_names), "source_type": "site", "category": "location"}
            ))
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
            group=QuestionGroup.EINSATZBEREICHE,
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
    
    Args:
        questions: Konsolidierte Fragen
        
    Returns:
        Gefilterte Liste von Fragen
    """
    logger.info("🎯 Stage 4: FILTER - Removing unwanted questions...")
    
    filtered = []
    seen_texts = set()
    
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
                metadata_items=classified_data.get('metadata', [])
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

