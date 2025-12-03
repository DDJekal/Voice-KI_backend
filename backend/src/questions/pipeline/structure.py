"""
Structure Pipeline Stage - 3-Tier Hybrid Approach mit Phasen-Struktur

Builds questions from three sources in priority order:
1. Protocol Questions (LLM-extracted from protocol)
2. Verbatim Candidates (Fallback for uncovered topics)
3. Generated Questions (Deterministic base questions)
4. Phase-basierte Standard-Questions (Motivation, Werdegang, Abschluss)

Port of src/pipeline/structure.ts with Hybrid enhancements.
"""

import logging
from typing import List, Set, Optional
import re

from ..types import (
    ExtractResult, 
    Question, 
    QuestionType, 
    QuestionGroup, 
    QuestionSource,
    ProtocolQuestion
)
from .phase_builder import (
    build_phase_2_questions,
    build_phase_4_questions,
    build_phase_5_questions,
    build_phase_6_questions
)

logger = logging.getLogger(__name__)


def _slugify(text: str) -> str:
    """Create URL-safe slug from text"""
    text = text.lower()
    text = re.sub(r'[äöüß]', lambda m: {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss'}[m.group()], text)
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')


def _refine_question_text(question_text: str, question_type: str = "boolean") -> str:
    """
    Verfeinert Fragetext für bessere Grammatik und natürlichen Sprachfluss.
    
    Korrigiert häufige Fehler:
    - "besonderes Interesse am Bereich X" → "Interessieren Sie sich für X"
    - "Sind Sie examinierte X oder Y" → "Haben Sie ein Examen als X/Y"
    - "bereit zu Schichtdienst" → "bereit, im Schichtdienst zu arbeiten"
    - Redundante "am Bereich" → "für"
    
    Args:
        question_text: Original-Fragetext
        question_type: Typ der Frage (boolean, choice, etc.)
        
    Returns:
        Verbesserter Fragetext
    """
    import re
    
    original = question_text  # Für Debugging
    
    # Fix 1: "besonderes Interesse am Bereich X" → "Interessieren Sie sich für X"
    if "besonderes interesse am bereich" in question_text.lower():
        match = re.search(r'am Bereich (.+)\?', question_text, re.IGNORECASE)
        if match:
            bereich = match.group(1).strip()
            # Artikel bestimmen (der/die/das)
            if any(word in bereich.lower() for word in ['station', 'abteilung', 'pflege']):
                artikel = "die"
            elif any(word in bereich.lower() for word in ['labor', 'zentrum', 'katheterlabor']):
                artikel = "das"
            else:
                artikel = "den"
            
            question_text = f"Interessieren Sie sich für {artikel} {bereich}?"
            logger.debug(f"  Refined (interest): '{original}' → '{question_text}'")
            return question_text
    
    # Fix 2: "Sind Sie examinierte X oder Y" → "Haben Sie ein Examen als X/Y"
    if "sind sie examinierte" in question_text.lower():
        match = re.search(r'examinierte?\s+(.+?)\s+oder\s+(.+)\?', question_text, re.IGNORECASE)
        if match:
            role1 = match.group(1).strip()
            role2 = match.group(2).strip()
            # Erkenne wenn es Pflegefachfrau/-mann ist
            if "pflegefach" in role1.lower():
                question_text = "Haben Sie ein abgeschlossenes Examen als Pflegefachfrau/-mann?"
            else:
                question_text = f"Haben Sie ein abgeschlossenes Examen als {role1} oder {role2}?"
            logger.debug(f"  Refined (qualification): '{original}' → '{question_text}'")
            return question_text
    
    # Fix 3: Entferne redundante "am Bereich" → "für"
    if " am bereich " in question_text.lower():
        question_text = re.sub(r'\s+am Bereich\s+', ' für ', question_text, flags=re.IGNORECASE)
        logger.debug(f"  Refined (redundancy): '{original}' → '{question_text}'")
    
    # Fix 4: "bereit zu Schichtdienst" → "bereit, im Schichtdienst zu arbeiten"
    if "bereit zu schicht" in question_text.lower():
        question_text = re.sub(
            r'bereit\s+zu\s+Schichtdienst', 
            'bereit, im Schichtdienst zu arbeiten', 
            question_text,
            flags=re.IGNORECASE
        )
        logger.debug(f"  Refined (shift work): '{original}' → '{question_text}'")
    
    # Fix 5: "Haben Sie Interesse am/an X" → "Interessieren Sie sich für X"
    if "haben sie interesse am" in question_text.lower() or "haben sie interesse an" in question_text.lower():
        match = re.search(r'Haben Sie Interesse (am|an|für)\s+(.+)\?', question_text, re.IGNORECASE)
        if match:
            bereich = match.group(2).strip()
            question_text = f"Interessieren Sie sich für {bereich}?"
            logger.debug(f"  Refined (interest v2): '{original}' → '{question_text}'")
    
    return question_text


def _detect_question_type(text: str, pq_type: Optional[str]) -> QuestionType:
    """
    Detect question type from text and protocol question type hint.
    
    Args:
        text: Question text
        pq_type: Type hint from ProtocolQuestion (if available)
    
    Returns:
        QuestionType enum value
    """
    # If we have a type hint from protocol, use it
    if pq_type:
        type_map = {
            "boolean": QuestionType.BOOLEAN,
            "choice": QuestionType.CHOICE,
            "multi_choice": QuestionType.MULTI_CHOICE,
            "string": QuestionType.STRING,
            "date": QuestionType.DATE
        }
        if pq_type in type_map:
            return type_map[pq_type]
    
    # Fallback: Detect from text patterns
    text_lower = text.lower()
    
    # Boolean indicators
    if any(text_lower.startswith(p) for p in ["haben sie", "sind sie", "können sie", "besitzen sie", "möchten sie"]):
        return QuestionType.BOOLEAN
    
    # Choice indicators
    if any(w in text_lower for w in ["welche", "welcher", "welches", "in welchem", "wo möchten"]):
        return QuestionType.CHOICE
    
    # Date indicators
    if any(w in text_lower for w in ["ab wann", "wann können", "datum"]):
        return QuestionType.DATE
    
    # Default to string
    return QuestionType.STRING


def _detect_question_group(category: Optional[str], text: str) -> QuestionGroup:
    """
    Detect question group from category or text.
    
    Args:
        category: Category from ProtocolQuestion (if available)
        text: Question text
    
    Returns:
        QuestionGroup enum value
    """
    if category:
        category_map = {
            "qualifikation": QuestionGroup.QUALIFIKATION,
            "erfahrung": QuestionGroup.QUALIFIKATION,
            "einsatzbereich": QuestionGroup.EINSATZBEREICH,
            "rahmen": QuestionGroup.RAHMEN,
            "praeferenzen": QuestionGroup.PRAEFERENZEN,
            "standort": QuestionGroup.STANDORT,
            "kontakt": QuestionGroup.KONTAKT
        }
        if category in category_map:
            return category_map[category]
    
    # Fallback: Detect from text
    text_lower = text.lower()
    
    if any(w in text_lower for w in ["examen", "abschluss", "qualifikation", "ausbildung", "zertifikat"]):
        return QuestionGroup.QUALIFIKATION
    
    if any(w in text_lower for w in ["erfahrung", "kenntnisse", "praxis", "berufserfahrung"]):
        return QuestionGroup.QUALIFIKATION
    
    if any(w in text_lower for w in ["abteilung", "bereich", "station", "fachabteilung", "einsatzbereich"]):
        return QuestionGroup.EINSATZBEREICH
    
    if any(w in text_lower for w in ["schicht", "arbeitszeit", "vollzeit", "teilzeit", "verfügbar"]):
        return QuestionGroup.RAHMEN
    
    if any(w in text_lower for w in ["standort", "ort", "wo möchten"]):
        return QuestionGroup.STANDORT
    
    return QuestionGroup.PRAEFERENZEN


def _is_name_or_address_question(text: str) -> bool:
    """Check if question is about name or address (should be skipped)"""
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


def _extract_street_name(address: str) -> str:
    """
    Extrahiert nur den Straßennamen aus einer vollständigen Adresse.
    
    Args:
        address: Vollständige Adresse (z.B. "Auerbachstraße 110, 70376 Stuttgart" 
                 oder "Standort Burgholzhof (Auerbachstraße 110, 70376 Stuttgart)")
        
    Returns:
        Nur Straßenname (z.B. "Auerbachstraße")
    """
    import re
    
    # Fall 1: "Standort XYZ (Straße ...)" → extrahiere nur Straßenname
    if "(" in address and ")" in address:
        # Extrahiere Inhalt zwischen Klammern
        match = re.search(r'\(([^)]+)\)', address)
        if match:
            address = match.group(1).strip()
    
    # Fall 2: "Straße Nummer, PLZ Stadt" → entferne alles nach Komma
    if "," in address:
        address = address.split(",")[0].strip()
    
    # Fall 3: Entferne Hausnummer (alles nach erstem Leerzeichen + Zahl)
    match = re.match(r'^([^\d]+)', address)
    if match:
        street = match.group(1).strip()
        return street
    
    return address


def _generate_site_preamble(sites: List) -> Optional[str]:
    """
    Generiert eine kontextuelle Einführung für Standort-Fragen.
    
    Args:
        sites: Liste der Standorte
        
    Returns:
        Preamble-Text oder None
    """
    if not sites or len(sites) <= 1:
        return None
    
    count = len(sites)
    
    # Extrahiere nur Straßennamen
    street_names = [_extract_street_name(site.label) for site in sites]
    
    if count == 2:
        # Beide nennen - professionell und einladend
        return f"Wir sind an zwei Standorten vertreten: in der {street_names[0]} und der {street_names[1]}."
    elif count == 3:
        # Alle drei nennen - professionell
        sites_str = f"{street_names[0]}, {street_names[1]} und {street_names[2]}"
        return f"Unser Klinikum hat drei Standorte: {sites_str}."
    else:
        # Nur Anzahl + erste 2 Beispiele - flexibel
        sites_str = f"{street_names[0]} und {street_names[1]}"
        return f"Wir können Ihnen Einsätze an {count} verschiedenen Standorten anbieten, unter anderem {sites_str}."


def _detect_department_terminology(all_departments: List[str]) -> str:
    """
    Erkennt automatisch die passende Begrifflichkeit basierend auf den Abteilungsnamen.
    
    Args:
        all_departments: Liste aller Abteilungen
        
    Returns:
        "Stationen" oder "Fachabteilungen"
    """
    if not all_departments:
        return "Fachabteilungen"
    
    # Keywords die auf Gesundheitswesen/Pflege hinweisen
    healthcare_keywords = [
        "station", "intensiv", "pflege", "op", "anästhesie", "chirurg",
        "kardiologie", "onkologie", "gynäkologie", "pädiatrie", "geriatrie",
        "reha", "palliativ", "dialyse", "kreißsaal", "imc", "stroke",
        "herzkatheterlabor", "endoskopie", "bronchologie", "nephrologie",
        "pneumologie", "gastroenterologie", "urologie", "orthopädie"
    ]
    
    # Zähle wie oft Healthcare-Keywords vorkommen
    healthcare_count = 0
    total_count = len(all_departments)
    
    for dept in all_departments:
        dept_lower = dept.lower()
        if any(keyword in dept_lower for keyword in healthcare_keywords):
            healthcare_count += 1
    
    # Wenn mehr als 30% der Abteilungen Healthcare-Keywords enthalten → "Stationen"
    if total_count > 0 and (healthcare_count / total_count) > 0.3:
        return "Stationen"
    
    return "Fachabteilungen"


def _generate_department_preamble(
    all_departments: List[str],
    priorities: List = None,
    is_healthcare: bool = True
) -> Optional[str]:
    """
    Generiert eine kontextuelle Einführung für Abteilungs-/Stationsfragen.
    
    Args:
        all_departments: Liste aller Abteilungen/Stationen
        priorities: Optional Liste von Prioritäts-Objekten
        is_healthcare: DEPRECATED - wird automatisch erkannt
        
    Returns:
        Tuple (preamble_text, term_singular) - Preamble und Singular-Begriff
    """
    if not all_departments:
        return None, "Fachabteilung"
    
    count = len(all_departments)
    
    # NEU: Automatische Erkennung der Begrifflichkeit
    term = _detect_department_terminology(all_departments)
    
    # Korrektes Singular: "Stationen" → "Station", "Fachabteilungen" → "Fachabteilung"
    if term == "Stationen":
        term_singular = "Station"
    else:
        term_singular = "Fachabteilung"
    
    # Basis-Preamble mit Anzahl - professionell und einladend
    if count <= 5:
        # Wenige Optionen - alle nennen
        if count == 2:
            preamble = f"Bei uns können Sie in {count} {term} eingesetzt werden: {all_departments[0]} und {all_departments[1]}."
        else:
            # 3-5 Optionen
            deps_str = ", ".join(all_departments[:-1]) + f" und {all_departments[-1]}"
            preamble = f"Wir bieten Einsätze in {count} {term} an: {deps_str}."
    elif count <= 10:
        # Mittlere Anzahl - erste 4-5 Beispiele nennen
        examples = all_departments[:5]
        examples_str = ", ".join(examples)
        preamble = f"Wir haben {count} verschiedene {term}, zum Beispiel {examples_str}."
    else:
        # Viele Optionen - nur Anzahl + 3-4 Beispiele - flexibel und einladend
        examples = all_departments[:4]
        examples_str = ", ".join(examples)
        preamble = f"Wir können Ihnen vielfältige Einsatzmöglichkeiten in {count} {term} anbieten, darunter {examples_str}."
    
    # Prioritäten hinzufügen, falls vorhanden
    if priorities and len(priorities) > 0:
        prio_names = [p.label for p in priorities[:2]]
        if len(prio_names) == 1:
            preamble += f" Aktuell besonders gesucht: {prio_names[0]}."
        else:
            preamble += f" Aktuell besonders gesucht: {' und '.join(prio_names)}."
    
    return preamble, term_singular


def build_questions(extract_result: ExtractResult) -> List[Question]:
    """
    Build questions using 3-Tier Hybrid Approach:
    
    Tier 1: Protocol Questions (LLM-extracted, highest priority)
    Tier 2: Verbatim Candidates (Fallback for uncovered topics)
    Tier 3: Generated Questions (Deterministic base questions)
    
    Args:
        extract_result: Extracted data from conversation protocol
        
    Returns:
        List of questions
    """
    questions: List[Question] = []
    covered_topics: Set[str] = set()  # Track which topics are already covered
    
    logger.info("Building questions using 4-Tier Hybrid Approach...")
    
    # ========================================
    # PRE-SCAN: Qualifikations-Konsolidierung prüfen
    # ========================================
    # Prüfe VOR allen anderen Tiers, ob mehrere Qualifikations-Alternativen vorliegen
    qualification_keywords = ['studium', 'abschluss', 'ausbildung', 'bachelor', 'master', 
                              'diplom', 'examen', 'zertifikat', 'qualifikation', 'fortbildung']
    
    all_qualifications = extract_result.must_have + extract_result.alternatives
    combined_text = ' '.join(all_qualifications).lower() if all_qualifications else ''
    
    # Prüfe ob es primär um Qualifikationen geht
    has_qualification_terms = any(keyword in combined_text for keyword in qualification_keywords)
    has_multiple_options = len(all_qualifications) >= 2
    qualification_consolidated = False
    
    if has_qualification_terms and has_multiple_options:
        logger.info(f"🎯 Detected {len(all_qualifications)} qualification alternatives - will consolidate")
        qualification_consolidated = True
        
        # Markiere Qualifikations-Topics als "geplant für Konsolidierung"
        # Diese werden bei Tier 1 Protocol Questions übersprungen
        covered_topics.add("qualifikation_consolidated")
    
    # ========================================
    # TIER 1: Protocol Questions (LLM-extracted)
    # ========================================
    tier1_count = 0
    
    for pq in extract_result.protocol_questions:
        # Skip name/address questions
        if _is_name_or_address_question(pq.text):
            logger.debug(f"Skipping name/address question: {pq.text[:50]}")
            continue
        
        # NEU: Skip qualification questions if consolidation is planned
        if qualification_consolidated:
            # Prüfe ob diese Frage qualifikationsbezogen ist
            question_lower = pq.text.lower()
            is_qualification_question = any(keyword in question_lower for keyword in qualification_keywords)
            
            if is_qualification_question:
                logger.debug(f"Skipping qualification question (will be consolidated): {pq.text[:60]}")
                continue
        
        # Detect type and group
        q_type = _detect_question_type(pq.text, pq.type)
        q_group = _detect_question_group(pq.category, pq.text)
        
        # Create question ID
        q_id = f"pq_{pq.page_id}_{pq.prompt_id or 0}"
        
        # Handle options for choice questions
        options = pq.options
        if q_type == QuestionType.CHOICE and not options:
            # Special case: "In welchem Bereich" → use all_departments
            if "bereich" in pq.text.lower() or "abteilung" in pq.text.lower() or "station" in pq.text.lower():
                options = extract_result.all_departments
        
        # Determine priority
        priority = 1 if pq.is_gate or pq.is_required else 2
        
        # NEU: Generiere Preamble für spezielle Frage-Typen
        preamble = None
        question_text = pq.text
        
        # Fall 1: Abteilungs/Stations-Fragen mit vielen Optionen
        if q_type == QuestionType.CHOICE and options and len(options) > 5:
            # Prüfe ob es um Abteilungen/Stationen geht
            if "abteilung" in pq.text.lower() or "bereich" in pq.text.lower() or "station" in pq.text.lower():
                preamble, term_singular = _generate_department_preamble(
                    options,
                    priorities=extract_result.priorities
                )
                
                # Ersetze Begrifflichkeit in der Frage mit dem erkannten Term
                question_text = pq.text.replace("Fachabteilung", term_singular)
                question_text = question_text.replace("fachabteilung", term_singular.lower())
                question_text = question_text.replace("Abteilung", term_singular)
                question_text = question_text.replace("abteilung", term_singular.lower())
                
                # Mache Frage geschlossen statt offen
                if question_text.startswith("In welcher"):
                    question_text = f"Möchten Sie gerne in einer unserer {options[0] if len(options) == 1 else term_singular} arbeiten?"
                    # Bessere geschlossene Formulierung
                    if len(options) > 1:
                        question_text = f"Haben Sie bereits eine Präferenz für eine bestimmte {term_singular}?"
        
        # Fall 2: Arbeitszeit-Fragen (Schichtdienst, etc.) - NEU!
        if any(keyword in pq.text.lower() for keyword in ["schicht", "arbeitszeit", "dienst", "vollzeit", "teilzeit"]):
            if not preamble:  # Nur wenn noch keine Preamble gesetzt
                # Natürliche Überleitung zum Thema Arbeitszeit
                preamble = "Ich würde nun gerne zum Arbeitszeitmodell kommen."
                
                # Verbessere die Frage für natürlicheren Gesprächsfluss
                if q_type == QuestionType.BOOLEAN:
                    # "Sind Sie bereit zu Schichtdienst?" → natürlicher
                    if "schicht" in pq.text.lower():
                        question_text = "Wären Sie grundsätzlich bereit, im Schichtdienst zu arbeiten?"
                        preamble += " In vielen unserer Bereiche arbeiten wir im Schichtbetrieb."
        
        # NEU: Grammatik-Refinement anwenden (Level 2 Optimierung)
        question_text = _refine_question_text(question_text, q_type.value)
        
        # Create question
        question = Question(
            id=q_id,
            question=question_text,
            type=q_type,
            preamble=preamble,  # NEU: Preamble auch für Tier 1
            options=options,
            required=pq.is_required,
            priority=priority,
            group=q_group,
            help_text=pq.help_text,
            source=QuestionSource(
                page_id=pq.page_id,
                prompt_id=pq.prompt_id,
                verbatim=True
            )
        )
        
        questions.append(question)
        
        # NEU: Besseres Topic-Tracking für Abteilungs/Stations-Fragen
        topic_slug = _slugify(pq.text[:30])
        covered_topics.add(topic_slug)
        
        # Wenn es eine Abteilungs/Stations-Frage ist, markiere alle verwandten Topics als covered
        if "abteilung" in pq.text.lower() or "bereich" in pq.text.lower() or "station" in pq.text.lower():
            covered_topics.add("abteilung")
            covered_topics.add("bereich")
            covered_topics.add("station")
            covered_topics.add("fachabteilung")
        
        tier1_count += 1
    
    logger.info(f"✓ Tier 1 (Protocol Questions): {tier1_count} questions")
    
    # ========================================
    # TIER 2: Verbatim Candidates (Fallback)
    # ========================================
    tier2_count = 0
    
    for vc in extract_result.verbatim_candidates:
        if not vc.is_real_question:
            continue
        
        # Skip name/address questions
        if _is_name_or_address_question(vc.text):
            continue
        
        # Check if topic already covered
        topic_slug = _slugify(vc.text[:30])
        if topic_slug in covered_topics:
            logger.debug(f"Skipping duplicate verbatim: {vc.text[:50]}")
            continue
        
        # Detect type and group
        q_type = _detect_question_type(vc.text, None)
        q_group = _detect_question_group(None, vc.text)
        
        # NEU: Grammatik-Refinement anwenden (Level 2 Optimierung)
        refined_text = _refine_question_text(vc.text, q_type.value)
        
        # Create question
        q_id = f"vc_{vc.page_id}_{vc.prompt_id or 0}"
        
        question = Question(
            id=q_id,
            question=refined_text,
            type=q_type,
            required=False,
            priority=2,
            group=q_group,
            source=QuestionSource(
                page_id=vc.page_id,
                prompt_id=vc.prompt_id,
                verbatim=True
            )
        )
        
        questions.append(question)
        covered_topics.add(topic_slug)
        
        tier2_count += 1
    
    logger.info(f"✓ Tier 2 (Verbatim Fallback): {tier2_count} questions")
    
    # ========================================
    # TIER 3: Generated Questions (Deterministic)
    # ========================================
    tier3_count = 0
    
    # 1. Standort (if not already covered)
    if "standort" not in covered_topics:
        if not extract_result.sites:
            questions.append(Question(
                id="site_request",
                question="An welchem Standort möchten Sie arbeiten?",
                type=QuestionType.STRING,
                required=True,
                priority=1,
                group=QuestionGroup.STANDORT
            ))
            tier3_count += 1
        elif len(extract_result.sites) == 1:
            questions.append(Question(
                id="site_confirmation",
                question=f"Unser Standort ist {extract_result.sites[0].label}. Passt das für Sie?",
                type=QuestionType.BOOLEAN,
                required=True,
                priority=1,
                group=QuestionGroup.STANDORT
            ))
            tier3_count += 1
        else:
            # Multiple sites - generate preamble
            preamble = _generate_site_preamble(extract_result.sites)
            
            # Verkürze Options auf nur Straßennamen
            site_options = [_extract_street_name(site.label) for site in extract_result.sites]
            
            # Geschlossene Frage statt offener
            questions.append(Question(
                id="site_choice",
                preamble=preamble,  # NEU: Kontextuelle Einführung
                question="Haben Sie bereits eine Präferenz für einen bestimmten Standort?",
                type=QuestionType.CHOICE,
                options=site_options,  # NEU: Nur Straßennamen
                required=True,
                priority=1,
                group=QuestionGroup.STANDORT
            ))
            tier3_count += 1
    
    # 2. Einsatzbereich/Department (if not already covered)
    if "abteilung" not in covered_topics and "bereich" not in covered_topics:
        if extract_result.all_departments:
            # Generate preamble with priorities (NEU: mit automatischer Begriffserkennung)
            preamble, term_singular = _generate_department_preamble(
                extract_result.all_departments,
                priorities=extract_result.priorities
            )
            
            # Geschlossene Frage statt offener
            questions.append(Question(
                id="department",
                preamble=preamble,  # NEU: Kontextuelle Einführung
                question=f"Haben Sie bereits eine Präferenz für eine bestimmte {term_singular}?",
                type=QuestionType.CHOICE,
                options=extract_result.all_departments,
                required=True,
                priority=1,
                group=QuestionGroup.EINSATZBEREICH,
                input_hint="Bitte eine Abteilung nennen."
            ))
            tier3_count += 1
    
    # 3. Qualifikations-Konsolidierung (NEU: Intelligente Gruppierung)
    # Erstelle konsolidierte Frage wenn in PRE-SCAN erkannt
    if qualification_consolidated and "qualifikation" not in covered_topics:
        logger.info(f"🎯 Creating consolidated qualification question from {len(all_qualifications)} alternatives")
        
        # Bereinige und formatiere Optionen
        cleaned_options = []
        for qual in all_qualifications:
            # Entferne führende Marker wie "Zwingend:", "Alternativ:", etc.
            cleaned = re.sub(r'^(zwingend|alternativ|wünschenswert|bevorzugt):\s*', '', qual, flags=re.I)
            cleaned = cleaned.strip()
            if cleaned and cleaned not in cleaned_options:
                cleaned_options.append(cleaned)
        
        # Füge "Anderer Abschluss" hinzu
        if "anderer" not in combined_text.lower():
            cleaned_options.append("Anderer Abschluss")
        
        # Erstelle konsolidierte Frage
        preamble = None
        if len(cleaned_options) > 3:
            preamble = "Ich würde gerne Ihre Qualifikation abklären."
        
        questions.append(Question(
            id="qualification_degree_consolidated",
            preamble=preamble,
            question="Welchen Abschluss haben Sie?",
            type=QuestionType.CHOICE,
            options=cleaned_options,
            required=True,
            priority=1,
            group=QuestionGroup.QUALIFIKATION,
            help_text="Bitte wählen Sie die Qualifikation, die am besten zu Ihrem Abschluss passt.",
            context="Konsolidierte Qualifikations-Frage aus Must-Have und Alternativen"
        ))
        tier3_count += 1
        
        # Markiere alle Qualifikationen als covered
        covered_topics.add("qualifikation")
        covered_topics.add("abschluss")
        covered_topics.add("studium")
        covered_topics.add("ausbildung")
        for qual in all_qualifications:
            covered_topics.add(_slugify(qual))
        
        logger.info(f"✓ Created consolidated qualification question with {len(cleaned_options)} options")
    
    # 4. Must-Have Kriterien (Gate Questions) - if not already covered
    for must_have in extract_result.must_have:
        slug = _slugify(must_have)
        if slug not in covered_topics:
            if re.search(r'pflegefach', must_have, re.I):
                # Originalfrage mit Grammatikfehler
                question_text = "Sind Sie examinierte Pflegefachfrau oder Pflegefachmann?"
                # Level 2 Optimierung: Grammatik-Refinement
                question_text = _refine_question_text(question_text, "boolean")
                
                questions.append(Question(
                    id="qualification_nursing",
                    question=question_text,
                    type=QuestionType.BOOLEAN,
                    required=True,
                    priority=1,
                    group=QuestionGroup.QUALIFIKATION,
                    context=f"Muss-Kriterium: {must_have}"
                ))
                tier3_count += 1
            else:
                question_text = f"Haben Sie: {must_have}?"
                # Level 2 Optimierung: Grammatik-Refinement
                question_text = _refine_question_text(question_text, "boolean")
                
                questions.append(Question(
                    id=f"gate_{slug}",
                    question=question_text,
                    type=QuestionType.BOOLEAN,
                    required=True,
                    priority=1,
                    group=QuestionGroup.QUALIFIKATION,
                    context=f"Muss-Kriterium: {must_have}"
                ))
                tier3_count += 1
    
    # 5. Alternativen (nur MFA und nicht-Qualifikations-Alternativen)
    for alt in extract_result.alternatives:
        slug = _slugify(alt)
        if slug not in covered_topics:
            if re.search(r'MFA', alt, re.I):
                # Natürlichere Formulierung mit Preamble
                preamble = "Ich hätte noch eine weitere Möglichkeit für Sie."
                
                questions.append(Question(
                    id="op_mfa_alternative",
                    preamble=preamble,
                    question="Wären Sie offen für eine MFA-Qualifizierungsmaßnahme für den OP-Bereich?",
                    type=QuestionType.BOOLEAN,
                    required=False,
                    priority=2,
                    group=QuestionGroup.QUALIFIKATION
                ))
                tier3_count += 1
    
    # 6. Prioritäten als Präferenzfragen (if not already covered)
    for prio in extract_result.priorities:
        slug = _slugify(prio.label)
        if slug not in covered_topics:
            # Originalfrage mit Grammatikfehler
            question_text = f"Haben Sie besonderes Interesse am Bereich {prio.label}?"
            # Level 2 Optimierung: Grammatik-Refinement
            question_text = _refine_question_text(question_text, "boolean")
            
            questions.append(Question(
                id=f"prio_{slug}",
                question=question_text,
                type=QuestionType.BOOLEAN,
                required=False,
                priority=prio.prio_level,
                group=QuestionGroup.PRAEFERENZEN,
                help_text=prio.reason
            ))
            tier3_count += 1
    
    # 7. Arbeitszeit (if not already covered and constraints available)
    if "arbeitszeit" not in covered_topics and extract_result.constraints and extract_result.constraints.arbeitszeit:
        vollzeit = extract_result.constraints.arbeitszeit.vollzeit
        teilzeit = extract_result.constraints.arbeitszeit.teilzeit
        
        if vollzeit and teilzeit:
            # Natürliche Preamble mit Überleitungsformulierung
            preamble = (
                "Ich würde nun gerne zum Arbeitszeitmodell kommen. "
                f"Wir bieten sowohl Vollzeit ({vollzeit}) als auch Teilzeit ({teilzeit}) an. "
                "Diese können wir auch individuell an Ihre Bedürfnisse anpassen."
            )
            
            questions.append(Question(
                id="arbeitszeit",
                preamble=preamble,
                question="Haben Sie bereits eine Präferenz bezüglich des Arbeitszeitmodells?",
                type=QuestionType.CHOICE,
                options=["Vollzeit", "Teilzeit", "Bin noch flexibel"],
                required=True,
                priority=2,
                group=QuestionGroup.RAHMEN
            ))
            tier3_count += 1
        elif vollzeit:
            preamble = "Ich möchte kurz auf das Arbeitszeitmodell eingehen."
            
            questions.append(Question(
                id="vollzeit_confirmation",
                preamble=preamble,
                question=f"Die Stelle ist in Vollzeit ({vollzeit}). Ist das für Sie passend?",
                type=QuestionType.BOOLEAN,
                required=True,
                priority=2,
                group=QuestionGroup.RAHMEN
            ))
            tier3_count += 1
    
    logger.info(f"✓ Tier 3 (Generated Questions): {tier3_count} questions")
    
    # ========================================
    # TIER 4: Phasen-basierte Standard-Questions
    # ========================================
    logger.info("Building Tier 4 (Phase-based Standard Questions)...")
    
    # Phase 2: Motivation & Erwartung
    phase_2_questions = build_phase_2_questions(extract_result)
    questions.extend(phase_2_questions)
    
    # Phase 4: Präferenzen (zusätzlich zu Tier 1-3)
    phase_4_questions = build_phase_4_questions(extract_result)
    questions.extend(phase_4_questions)
    
    # Phase 5: Werdegang & Startdatum
    phase_5_questions = build_phase_5_questions(extract_result)
    questions.extend(phase_5_questions)
    
    # Phase 6: Erreichbarkeit
    phase_6_questions = build_phase_6_questions()
    questions.extend(phase_6_questions)
    
    tier4_count = len(phase_2_questions) + len(phase_4_questions) + len(phase_5_questions) + len(phase_6_questions)
    logger.info(f"✓ Tier 4 (Phase-based Questions): {tier4_count} questions")
    
    # ========================================
    # Summary
    # ========================================
    total = len(questions)
    logger.info(f"✓ TOTAL: {total} questions built ({tier1_count} Protocol + {tier2_count} Verbatim + {tier3_count} Generated + {tier4_count} Phase-based)")
    
    return questions
