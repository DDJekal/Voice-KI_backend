"""
Phase-basierte Question-Generierung

Erstellt Questions für die 6 Gesprächsphasen basierend auf den Masterprompt.txt
"""

from typing import List, Dict, Any
from ..types import Question, ExtractResult, QuestionType

import logging

logger = logging.getLogger(__name__)


def build_phase_2_questions(extract_result: ExtractResult) -> List[Question]:
    """
    Generiert offene Motivation-Fragen + weiche Gates für Phase 2.
    
    Phase 2: Motivation & Erwartung (systemisch)
    - 3-4 offene Fragen zu Beweggründen
    - Weiche Gate-Fragen ("damit ich das einordnen kann...")
    
    Args:
        extract_result: Extract-Ergebnis mit motivation_dimensions
    
    Returns:
        Liste von Questions für Phase 2
    """
    questions = []
    
    # Standard-Motivationsfragen (immer dabei)
    motivation_base = [
        Question(
            id="motivation_reason",
            question="Was war für Sie der wichtigste Grund, sich zu bewerben?",
            type=QuestionType.STRING,
            phase=2,
            preamble="Vielleicht können Sie mir ein wenig erzählen",
            required=False,
            priority=1,
            group="Motivation",
            context="Offene Frage zu Beweggründen",
            category="motivation",
            category_order=1
        ),
        Question(
            id="motivation_expectations",
            question="Was ist Ihnen bei Ihrem nächsten Arbeitgeber besonders wichtig?",
            type=QuestionType.STRING,
            phase=2,
            required=False,
            priority=1,
            group="Motivation",
            context="Erwartungen an Arbeitgeber",
            category="motivation",
            category_order=1
        ),
        Question(
            id="motivation_change",
            question="Was wünschen Sie sich von einer Veränderung im Vergleich zu Ihrer aktuellen Situation?",
            type=QuestionType.STRING,
            phase=2,
            required=False,
            priority=1,
            group="Motivation",
            context="Veränderungswunsch",
            category="motivation",
            category_order=1
        )
    ]
    
    questions.extend(motivation_base)
    
    # Weiche Gate-Fragen basierend auf must_have
    if extract_result.must_have:
        for i, must_have in enumerate(extract_result.must_have[:2]):  # Max 2 weiche Gates
            question_id = f"gate_soft_{must_have.lower().replace(' ', '_').replace('/', '_')[:40]}"
            
            # Formuliere weiche Frage
            if "abschluss" in must_have.lower() or "ausbildung" in must_have.lower():
                question_text = "Welche Ausbildung haben Sie abgeschlossen?"
                preamble = "Damit ich Ihren fachlichen Hintergrund einordnen kann"
            elif "erfahrung" in must_have.lower():
                question_text = "Wie lange arbeiten Sie schon in diesem Bereich ungefähr?"
                preamble = "Um ein besseres Bild zu bekommen"
            elif "deutsch" in must_have.lower() or "sprach" in must_have.lower():
                question_text = "Wie würden Sie Ihr Sprachniveau in Deutsch selbst einschätzen?"
                preamble = "Damit ich das einordnen kann"
            else:
                question_text = f"Haben Sie: {must_have}?"
                preamble = "Eine kurze Frage dazu"
            
            questions.append(Question(
                id=question_id,
                question=question_text,
                type=QuestionType.STRING,
                phase=2,
                preamble=preamble,
                required=False,
                priority=2,
                group="Qualifikation",
                context=f"Weiches Gate für: {must_have}",
                category="standardqualifikationen",
                category_order=3
            ))
    
    logger.info(f"Generated {len(questions)} questions for Phase 2 (Motivation)")
    return questions


def build_phase_4_questions(extract_result: ExtractResult) -> List[Question]:
    """
    Generiert Präferenz-Fragen + konkrete Gates für Phase 4.
    
    Phase 4: Präferenzen & Rahmenbedingungen
    - Einsatzbereiche, Arbeitszeitmodell
    - Konkrete Gate-Prüfungen
    
    Args:
        extract_result: Extract-Ergebnis
    
    Returns:
        Liste von Questions für Phase 4
    """
    questions = []
    
    # Einsatzbereich-Frage (wenn Departments vorhanden)
    if extract_result.all_departments:
        questions.append(Question(
            id="preference_department",
            question="In welchem Bereich würden Sie am liebsten arbeiten?",
            type=QuestionType.CHOICE,
            phase=4,
            preamble="Damit ich ein gutes Bild bekomme, was für Sie im Arbeitsalltag passt",
            options=extract_result.all_departments[:10],  # Max 10 Optionen
            required=False,
            priority=2,
            group="Präferenzen",
            context="Einsatzbereich-Präferenz",
            category="praeferenzen",
            category_order=4
        ))
    
    # Arbeitszeit-Frage (wenn Constraints vorhanden)
    if extract_result.constraints.arbeitszeit:
        arbeitszeit = extract_result.constraints.arbeitszeit
        options = []
        if arbeitszeit.vollzeit:
            options.append(f"Vollzeit ({arbeitszeit.vollzeit})")
        if arbeitszeit.teilzeit:
            options.append(f"Teilzeit ({arbeitszeit.teilzeit})")
        
        if options:
            questions.append(Question(
                id="preference_worktime",
                question="Welches Arbeitszeitmodell würde für Sie am besten passen?",
                type=QuestionType.CHOICE,
                phase=4,
                preamble="Für die Planung ist das wichtig",
                options=options,
                required=False,
                priority=2,
                group="Rahmen",
                context="Arbeitszeitmodell",
                category="rahmenbedingungen",
                category_order=2
            ))
    
    # Schichtbereitschaft (wenn in Constraints)
    if extract_result.constraints.schichten:
        questions.append(Question(
            id="preference_shifts",
            question="Wären Sie grundsätzlich bereit, im Schichtdienst zu arbeiten?",
            type=QuestionType.BOOLEAN,
            phase=4,
            preamble="Eine kurze Frage zu den Rahmenbedingungen",
            required=False,
            priority=2,
            group="Rahmen",
            context=f"Schichtmodell: {extract_result.constraints.schichten}",
            category="rahmenbedingungen",
            category_order=2
        ))
    
    logger.info(f"Generated {len(questions)} questions for Phase 4 (Präferenzen)")
    return questions


def build_phase_5_questions(extract_result: ExtractResult) -> List[Question]:
    """
    Generiert Werdegang-Fragen für Phase 5.
    
    Phase 5: Werdegang & Startdatum
    - Max. 3 berufliche Stationen (antichronologisch)
    - Name, Zeitraum (Monat/Jahr), Tätigkeiten
    - Startdatum
    
    Args:
        extract_result: Extract-Ergebnis
    
    Returns:
        Liste von Questions für Phase 5
    """
    questions = []
    
    if not extract_result.career_questions_needed:
        logger.info("Career questions not needed, skipping Phase 5 questions")
        return questions
    
    # Werdegang-Stationen (max 3)
    career_stations = [
        Question(
            id="career_station_1",
            question="Wo waren Sie zuletzt tätig?",
            type=QuestionType.STRING,
            phase=5,
            preamble="Damit ich Ihr Profil vollständig einordnen kann",
            required=False,
            priority=3,
            group="Werdegang",
            context="Letzte Station: Name der Einrichtung, Zeitraum (Monat/Jahr), Tätigkeiten",
            category="werdegang",
            category_order=5,
            help_text="Bitte Name der Einrichtung, von wann bis wann (Monat und Jahr), und welche Aufgaben"
        ),
        Question(
            id="career_station_2",
            question="Und davor – wo waren Sie da beschäftigt?",
            type=QuestionType.STRING,
            phase=5,
            required=False,
            priority=3,
            group="Werdegang",
            context="Vorherige Station: Name, Zeitraum, Tätigkeiten",
            category="werdegang",
            category_order=5
        ),
        Question(
            id="career_station_3",
            question="Gab es davor noch eine Station, die für uns wichtig sein könnte?",
            type=QuestionType.STRING,
            phase=5,
            required=False,
            priority=3,
            group="Werdegang",
            context="Weitere relevante Station (optional)",
            category="werdegang",
            category_order=5
        )
    ]
    
    questions.extend(career_stations)
    
    # Startdatum
    questions.append(Question(
        id="availability_start",
        question="Ab wann könnten Sie frühestens bei uns starten?",
        type=QuestionType.DATE,
        phase=5,
        required=False,
        priority=3,
        group="Verfügbarkeit",
        context="Frühestes Startdatum",
        category="verfuegbarkeit",
        category_order=6
    ))
    
    logger.info(f"Generated {len(questions)} questions for Phase 5 (Werdegang)")
    return questions


def build_phase_6_questions() -> List[Question]:
    """
    Generiert Abschluss-Fragen für Phase 6.
    
    Phase 6: Erreichbarkeit, Zusammenfassung & Abschluss
    - Rückruf-Fenster (keine Telefonnummer)
    
    Returns:
        Liste von Questions für Phase 6
    """
    questions = [
        Question(
            id="contact_callback_time",
            question="Wann passt es Ihnen telefonisch meistens am besten?",
            type=QuestionType.CHOICE,
            phase=6,
            preamble="Damit wir Sie gut erreichen können",
            options=["Vormittags", "Nachmittags", "Früher Abend", "Flexibel"],
            required=False,
            priority=3,
            group="Kontakt",
            context="Bevorzugtes Rückruf-Fenster",
            category="kontakt",
            category_order=7
        )
    ]
    
    logger.info(f"Generated {len(questions)} questions for Phase 6 (Abschluss)")
    return questions

