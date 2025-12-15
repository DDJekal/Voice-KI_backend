"""
Structure Pipeline Stage - 3-Tier Hybrid Approach (Optimiert für ElevenLabs)

Builds questions from three sources in priority order:
1. Protocol Questions (LLM-extracted from protocol)
2. Verbatim Candidates (Fallback for uncovered topics)
3. Generated Questions (Deterministic base questions)

Phase 2, 5, 6 sind bereits in ElevenLabs verpromptet und werden NICHT generiert.

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
# phase_builder ist nicht mehr nötig - Phasen sind in ElevenLabs verpromptet

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


def _extract_location_info(address: str) -> dict:
    """
    Extrahiert Stadt, Straße und optional Stadtteil aus einer Adresse.
    
    Args:
        address: Vollständige Adresse (z.B. "Hohenheimerstraße 21, 70184 Stuttgart"
                 oder "Standort Burgholzhof (Auerbachstraße 110, 70376 Stuttgart)"
                 oder "Standortmöglichkeit a) Hohenheimerstraße 21, 70184 Stuttgart. Bereich: Geriatrie")
        
    Returns:
        Dict mit {"city": "Stuttgart", "street": "Hohenheimerstraße", "district": None, "plz": "70184"}
    """
    import re
    
    # Bereinigung: Entferne "Standortmöglichkeit a/b/c)" am Anfang
    address = re.sub(r'^[Ss]tandortmöglichkeit\s+[a-z]\)\s*', '', address)
    
    # Bereinigung: Entferne ". Bereich: ..." am Ende
    address = re.sub(r'\.\s*Bereich:.*$', '', address)
    
    # Fall 1: "Standort XYZ (Straße ...)" → extrahiere Inhalt zwischen Klammern
    if "(" in address and ")" in address:
        match = re.search(r'\(([^)]+)\)', address)
        if match:
            address = match.group(1).strip()
    
    # Bereinigung: Entferne "Standort XYZ, " am Anfang
    address = re.sub(r'^Standort\s+[^,]+,\s*', '', address)
    
    # Muster: "Straße Nummer, PLZ Stadt" oder "Straße Nummer, PLZ Stadt-Stadtteil"
    # Beispiele:
    # - "Hohenheimerstraße 21, 70184 Stuttgart"
    # - "Auerbachstraße 110, 70376 Stuttgart"
    # - "Am Fichtenkamp 7-9, Bünde"
    
    # Versuch 1: Mit PLZ
    match = re.search(r'^([A-ZÄÖÜa-zäöü\s]+?)\s+[\d\-]+\s*,\s*(\d{5})?\s*(.+?)$', address)
    if match:
        street = match.group(1).strip()
        plz = match.group(2)
        city_raw = match.group(3).strip() if match.group(3) else ""
        
        # Stadtteil aus Stadt extrahieren (z.B. "Stuttgart-Mitte" → Stadt: "Stuttgart", Stadtteil: "Mitte")
        district = None
        city = city_raw
        if '-' in city_raw and not city_raw.startswith('Bad '):  # "Bad Cannstatt" nicht splitten
            parts = city_raw.split('-', 1)
            city = parts[0].strip()
            district = parts[1].strip() if len(parts) > 1 else None
        
        return {
            "city": city, 
            "street": street, 
            "district": district, 
            "plz": plz,
            "full_address": address
        }
    
    # Versuch 2: Ohne PLZ (z.B. "Am Fichtenkamp 7-9, Bünde")
    match = re.search(r'^([A-ZÄÖÜa-zäöü\s]+?)\s+[\d\-]+\s*,\s*(.+?)$', address)
    if match:
        street = match.group(1).strip()
        city = match.group(2).strip()
        
        return {
            "city": city,
            "street": street,
            "district": None,
            "plz": None,
            "full_address": address
        }
    
    # Fallback: Nur Stadt
    return {
        "city": address,
        "street": None,
        "district": None,
        "plz": None,
        "full_address": address
    }


def _generate_smart_site_options(sites: List) -> tuple:
    """
    Intelligente Standort-Optionen basierend auf Städten.
    
    Strategie:
    - Wenn alle Standorte in derselben Stadt: Straßennamen verwenden
    - Wenn verschiedene Städte: Städtenamen verwenden
    - Optional mit Stadtteilen, wenn vorhanden
    
    Args:
        sites: Liste der Standorte
        
    Returns:
        Tuple (preamble, options, question)
    """
    if not sites:
        return None, [], "An welchem Standort möchten Sie arbeiten?"
    
    # Extrahiere Location-Infos für alle Sites
    locations = [_extract_location_info(site.label) for site in sites]
    
    # Prüfe: Sind alle in derselben Stadt?
    cities = set(loc['city'] for loc in locations if loc['city'] and loc['city'].strip())
    
    # Debug-Info
    logger.debug(f"Site options: {len(sites)} sites, {len(cities)} unique cities: {cities}")
    logger.debug(f"Extracted streets: {[loc['street'] for loc in locations]}")
    
    # Wenn alle Locations eine Stadt haben und es dieselbe ist
    if len(cities) == 1 and len(sites) > 1:
        # FALL 1: Alle in derselben Stadt → NUR Straßennamen verwenden
        city = list(cities)[0]
        options = [loc['street'] if loc['street'] else loc['city'] for loc in locations]
        
        # Entferne Duplikate (falls mehrere Standorte in gleicher Straße)
        unique_options = []
        seen = set()
        for opt in options:
            if opt and opt.strip() and opt not in seen:
                unique_options.append(opt)
                seen.add(opt)
        options = unique_options
        
        # Preamble: Nur Stadt nennen, nicht die einzelnen Straßen auflisten
        if len(sites) == 2:
            preamble = f"Wir sind an zwei Standorten in {city} vertreten."
        elif len(sites) == 3:
            preamble = f"Wir sind an drei Standorten in {city} vertreten."
        else:
            preamble = f"Wir sind an {len(sites)} Standorten in {city} vertreten."
        
        question = "Welcher Standort wäre für Sie am besten erreichbar?"
    
    # Wenn manche Sites keine Stadt haben oder leer sind, prüfe ob trotzdem alle in gleicher Stadt
    elif len(cities) <= 1 and len(sites) > 1:
        # Fallback: Wahrscheinlich Parse-Problem, nutze Straßen wenn vorhanden
        streets = [loc['street'] for loc in locations if loc['street']]
        if len(streets) == len(sites):
            # Alle haben Straßen → nutze die
            city = list(cities)[0] if cities else "verschiedenen Orten"
            options = streets
            
            if len(sites) == 2:
                preamble = f"Wir sind an zwei Standorten in {city} vertreten."
            elif len(sites) == 3:
                preamble = f"Wir sind an drei Standorten in {city} vertreten."
            else:
                preamble = f"Wir sind an {len(sites)} Standorten in {city} vertreten."
            
            question = "Welcher Standort wäre für Sie am besten erreichbar?"
        else:
            # Fallback auf Originaltext
            options = [loc['full_address'] for loc in locations]
            preamble = f"Wir haben {len(sites)} Standorte."
            question = "Welcher Standort passt für Sie am besten?"
    
    elif len(cities) > 1:
        # FALL 2: Verschiedene Städte → Städte verwenden
        options = [loc['city'] for loc in locations]
        
        # Entferne Duplikate
        unique_options = []
        seen = set()
        for opt in options:
            if opt not in seen:
                unique_options.append(opt)
                seen.add(opt)
        options = unique_options
        
        if len(cities) == 2:
            cities_list = list(cities)
            preamble = f"Wir sind an zwei Standorten vertreten: in {cities_list[0]} und {cities_list[1]}."
        elif len(cities) == 3:
            cities_list = list(cities)
            preamble = f"Wir haben drei Standorte: {', '.join(cities_list[:-1])} und {cities_list[-1]}."
        else:
            preamble = f"Wir haben {len(cities)} verschiedene Standorte."
        
        question = "Haben Sie bereits eine Präferenz für einen bestimmten Standort?"
    
    else:
        # FALL 3: Nur ein Standort (wird eh nicht als Choice gefragt, aber Fallback)
        options = [locations[0]['city']]
        preamble = None
        question = f"Unser Standort ist in {locations[0]['city']}. Passt das für Sie?"
    
    return preamble, options, question


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
    
    Phase 2 (Motivation), Phase 5 (Werdegang), Phase 6 (Verfügbarkeit/Kontakt)
    sind bereits in ElevenLabs verpromptet und werden NICHT generiert.
    
    Args:
        extract_result: Extracted data from conversation protocol
        
    Returns:
        List of questions
    """
    questions: List[Question] = []
    covered_topics: Set[str] = set()  # Track which topics are already covered
    
    logger.info("Building questions using 3-Tier Hybrid Approach (ElevenLabs-optimiert)...")
    
    # ========================================
    # PRE-SCAN: Qualifikations-Konsolidierung prüfen
    # ========================================
    # Prüfe VOR allen anderen Tiers, ob mehrere Qualifikations-Alternativen vorliegen
    qualification_keywords = ['studium', 'abschluss', 'ausbildung', 'bachelor', 'master', 
                              'diplom', 'examen', 'zertifikat', 'qualifikation', 'fortbildung']
    
    # NEU: Deutschkenntnisse-Keywords separat behandeln
    german_language_keywords = ['deutsch', 'sprachkenntnisse', 'sprachniveau', 'b2', 'c1', 'c2']
    
    # Sammle NUR Alternatives für Konsolidierung (NICHT Must-Haves!)
    all_qualifications = []
    has_german_requirement = False
    
    # Must-Haves werden NICHT konsolidiert - jedes wird zur eigenen Gate-Question
    # NUR Alternatives werden konsolidiert
    for item in extract_result.alternatives:
        item_lower = item.lower()
        # Prüfe ob es um Deutschkenntnisse geht
        if any(keyword in item_lower for keyword in german_language_keywords):
            has_german_requirement = True
            continue  # Skip - wird als separate Frage behandelt
        # Ansonsten zu Qualifikationen hinzufügen
        all_qualifications.append(item)
    
    # Prüfe Must-Haves separat auf Deutschkenntnisse
    for item in extract_result.must_have:
        item_lower = item.lower()
        if any(keyword in item_lower for keyword in german_language_keywords):
            has_german_requirement = True
            break
    
    # Prüfe auch protocol_questions auf Deutschkenntnisse
    for pq in extract_result.protocol_questions:
        pq_lower = pq.text.lower()
        if any(keyword in pq_lower for keyword in german_language_keywords):
            has_german_requirement = True
            break
    
    combined_text = ' '.join(all_qualifications).lower() if all_qualifications else ''
    
    # Prüfe ob es primär um Qualifikationen geht
    has_qualification_terms = any(keyword in combined_text for keyword in qualification_keywords)
    has_multiple_options = len(all_qualifications) >= 2
    qualification_consolidated = False
    
    if has_qualification_terms and has_multiple_options:
        logger.info(f"🎯 Detected {len(all_qualifications)} qualification ALTERNATIVES - will consolidate (Must-Haves stay separate)")
        qualification_consolidated = True
        
        # Markiere Qualifikations-Topics als "geplant für Konsolidierung"
        # Diese werden bei Tier 1 Protocol Questions übersprungen
        covered_topics.add("qualifikation_consolidated")
    
    if has_german_requirement:
        logger.info("🎯 Detected German language requirement - will create separate question")
    
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
        
        # NEU: Skip German language questions if has_german_requirement
        if has_german_requirement:
            question_lower = pq.text.lower()
            is_german_question = any(keyword in question_lower for keyword in german_language_keywords)
            
            if is_german_question:
                logger.debug(f"Skipping German language question (will be handled separately): {pq.text[:60]}")
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
        
        # Fall 3: Deutschkenntnisse - systemisch & offen (NEU!)
        if any(keyword in pq.text.lower() for keyword in ["deutsch", "sprachkenntnisse", "sprachniveau"]):
            if "b2" in pq.text.lower() or "niveau" in pq.text.lower():
                # Systemische, offene Formulierung statt geschlossener Boolean-Frage
                question_text = "Wie würden Sie Ihre Deutschkenntnisse einschätzen? Sind Sie Muttersprachler oder verfügen Sie mindestens über Kenntnisse auf B2-Niveau?"
                q_type = QuestionType.STRING  # Offene Frage für systemisches Gespräch
                preamble = "Damit ich Ihren sprachlichen Hintergrund einordnen kann"
        
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
        
        # NEU: Wenn es eine Vollzeit/Teilzeit-Frage ist, markiere arbeitszeit als covered
        if "vollzeit" in pq.text.lower() or "teilzeit" in pq.text.lower() or "arbeitszeit" in pq.text.lower():
            covered_topics.add("arbeitszeit")
            covered_topics.add("vollzeit")
            covered_topics.add("teilzeit")
        
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
            # Ein Standort - nur Stadt nennen
            location = _extract_location_info(extract_result.sites[0].label)
            
            questions.append(Question(
                id="site_confirmation",
                question=f"Unser Standort ist in {location['city']}. Passt das für Sie?",
                type=QuestionType.BOOLEAN,
                required=True,
                priority=1,
                group=QuestionGroup.STANDORT,
                context=f"Vollständige Adresse: {location['full_address']}"  # Für Nachfragen
            ))
            tier3_count += 1
        else:
            # Mehrere Standorte - intelligente Optionen
            preamble, site_options, site_question = _generate_smart_site_options(extract_result.sites)
            
            questions.append(Question(
                id="site_choice",
                preamble=preamble,
                question=site_question,
                type=QuestionType.CHOICE,
                options=site_options,
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
        
        # KEIN "Anderer Abschluss" - zu formal, nicht systemisch
        # Die KI soll natürlich nachfragen, wenn keine Option passt
        
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
            # KEIN help_text - passt nicht zum systemischen Gesprächsflow
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
    
    # 3b. Deutschkenntnisse-Frage (separat von Qualifikations-Konsolidierung)
    if has_german_requirement and "deutschkenntnisse" not in covered_topics:
        questions.append(Question(
            id="german_language_skills",
            preamble="Damit ich Ihren sprachlichen Hintergrund einordnen kann",
            question="Wie würden Sie Ihre Deutschkenntnisse einschätzen? Sind Sie Muttersprachler oder verfügen Sie mindestens über Kenntnisse auf B2-Niveau?",
            type=QuestionType.STRING,
            required=True,
            priority=1,
            group=QuestionGroup.QUALIFIKATION,
            context="Deutschkenntnisse-Anforderung aus Protokoll"
        ))
        tier3_count += 1
        covered_topics.add("deutschkenntnisse")
        covered_topics.add("deutsch")
        covered_topics.add("sprachkenntnisse")
        logger.info(f"✓ Created separate German language skills question")
    
    # 4. Must-Have Kriterien mit intelligenter Kategorisierung (Gate Questions)
    # Kategorisierungs-Keywords für Must-Have Kriterien
    driving_license_keywords = ['führerschein', 'fahrerlaubnis', 'pkw', 'klasse b', 'führerschein klasse']
    health_keywords = ['impfung', 'impfnachweis', 'masern', 'gesundheit', 'immunisierung', 'impfpass']
    soft_skill_keywords = ['bereitschaft', 'flexibilität', 'teamfähigkeit', 'kommunikation']
    
    for must_have in extract_result.must_have:
        slug = _slugify(must_have)
        
        # Skip if already covered
        if slug not in covered_topics:
            must_have_lower = must_have.lower()
            
            # Skip Deutschkenntnisse - werden separat behandelt
            if any(keyword in must_have_lower for keyword in german_language_keywords):
                logger.debug(f"Skipping German language must-have (handled separately): {must_have}")
                continue
            
            # Kategorisiere das Must-Have
            detected_category = None
            detected_group = QuestionGroup.QUALIFIKATION  # Default
            question_text = None
            
            # 1. Führerschein
            if any(keyword in must_have_lower for keyword in driving_license_keywords):
                detected_category = "fuehrerschein"
                detected_group = QuestionGroup.QUALIFIKATION
                question_text = f"Haben Sie {must_have}?"
                logger.debug(f"✓ Categorized as driving license: {must_have}")
            
            # 2. Gesundheit/Impfung
            elif any(keyword in must_have_lower for keyword in health_keywords):
                detected_category = "gesundheit"
                detected_group = QuestionGroup.QUALIFIKATION
                question_text = f"Verfügen Sie über {must_have}?"
                logger.debug(f"✓ Categorized as health requirement: {must_have}")
            
            # 3. Soft Skills / Bereitschaft
            elif any(keyword in must_have_lower for keyword in soft_skill_keywords):
                detected_category = "soft_skills"
                detected_group = QuestionGroup.RAHMEN  # Rahmenbedingungen
                
                # Natürlichere Formulierung
                if 'bereitschaft' in must_have_lower:
                    # "Bereitschaft zu X" → "Wären Sie bereit zu X?"
                    question_text = must_have.replace('Bereitschaft', 'Wären Sie bereit')
                    if not question_text.endswith('?'):
                        question_text += '?'
                else:
                    question_text = f"Ist Ihnen wichtig: {must_have}?"
                
                logger.debug(f"✓ Categorized as soft skill: {must_have}")
            
            # 4. Pflegefachkraft (Spezialfall)
            elif re.search(r'pflegefach', must_have, re.I):
                detected_category = "pflege_qualifikation"
                detected_group = QuestionGroup.QUALIFIKATION
                question_text = "Sind Sie examinierte Pflegefachfrau oder Pflegefachmann?"
                logger.debug(f"✓ Categorized as nursing qualification: {must_have}")
            
            # 5. FALLBACK für unbekannte Must-Haves
            else:
                detected_category = "sonstige_anforderung"
                detected_group = QuestionGroup.ZUSAETZLICHE_INFORMATIONEN
                
                # Intelligentere Formulierung statt "Haben Sie: X?"
                # Verhindert, dass es als Abschluss interpretiert wird
                question_text = f"Erfüllen Sie folgende Anforderung: {must_have}?"
                
                logger.warning(f"⚠️ Uncategorized must-have (using fallback): {must_have}")
            
            # Level 2 Optimierung: Grammatik-Refinement
            question_text = _refine_question_text(question_text, "boolean")
            
            # Erstelle Frage mit spezifischer Kategorie
            questions.append(Question(
                id=f"gate_{slug}",
                question=question_text,
                type=QuestionType.BOOLEAN,
                required=True,
                priority=1,
                group=detected_group,
                context=f"Muss-Kriterium ({detected_category}): {must_have}"
            ))
            
            tier3_count += 1
            covered_topics.add(slug)
            
            # Markiere Kategorie-spezifische Topics als covered
            if detected_category:
                covered_topics.add(detected_category)
    
    # 5. Alternativen (nur MFA und nicht-Qualifikations-Alternativen)
    for alt in extract_result.alternatives:
        slug = _slugify(alt)
        
        # Skip if already covered
        if slug not in covered_topics:
            # Skip Deutschkenntnisse - werden separat behandelt
            alt_lower = alt.lower()
            if any(keyword in alt_lower for keyword in german_language_keywords):
                logger.debug(f"Skipping German language alternative (handled separately): {alt}")
                continue
            
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
    # TIER 4: Phasen-basierte Standard-Questions (DEAKTIVIERT)
    # ========================================
    # Phase 2, 5, 6 sind bereits in ElevenLabs verpromptet!
    # Nur Protokoll-relevante Fragen (Tier 1-3) werden generiert.
    tier4_count = 0
    logger.info("✓ Tier 4 (Phase-based Questions): DISABLED - phases are hardcoded in ElevenLabs prompts")
    
    # ========================================
    # Summary
    # ========================================
    total = len(questions)
    logger.info(f"✓ TOTAL: {total} questions built ({tier1_count} Protocol + {tier2_count} Verbatim + {tier3_count} Generated)")
    
    return questions