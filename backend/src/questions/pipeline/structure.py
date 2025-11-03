"""
Structure Pipeline Stage

Deterministic creation of base questions from extract result.
Port of src/pipeline/structure.ts (simplified version)
"""

import logging
from typing import List
import re

from ..types import ExtractResult, Question, QuestionType, QuestionGroup, Condition, ConditionWhen, ConditionThen

logger = logging.getLogger(__name__)


def _slugify(text: str) -> str:
    """Create URL-safe slug from text"""
    text = text.lower()
    text = re.sub(r'[äöüß]', lambda m: {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss'}[m.group()], text)
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')


def build_questions(extract_result: ExtractResult) -> List[Question]:
    """
    Build base questions from extract result.
    
    This is deterministic - no LLM calls, just rule-based logic.
    
    Args:
        extract_result: Extracted data from conversation protocol
        
    Returns:
        List of questions
    """
    questions: List[Question] = []
    
    logger.info("Building base questions from extract result...")
    
    # 1. Identifikation - Name confirmation
    questions.append(Question(
        id="name_confirmation",
        question="Spreche ich mit {{first_name}} {{last_name}}?",
        type=QuestionType.BOOLEAN,
        required=True,
        priority=1,
        group=QuestionGroup.KONTAKT,
        context="Identifikation des Bewerbers"
    ))
    
    # 2. Adresse (conditional based on has_address)
    questions.append(Question(
        id="address_confirmation",
        question="Ich habe Ihre Adresse als {{street}} {{house_number}}, {{postal_code}} {{city}}. Ist das korrekt?",
        type=QuestionType.BOOLEAN,
        required=True,
        priority=1,
        group=QuestionGroup.KONTAKT,
        conditions=[Condition(
            when=ConditionWhen(field="has_address", op="eq", value=True),
            then=ConditionThen(action="ask")
        )]
    ))
    
    questions.append(Question(
        id="address_request",
        question="Nennen Sie mir bitte Ihre vollständige Adresse mit Straße, Hausnummer, PLZ und Ort.",
        type=QuestionType.STRING,
        required=True,
        priority=1,
        group=QuestionGroup.KONTAKT,
        conditions=[Condition(
            when=ConditionWhen(field="has_address", op="eq", value=False),
            then=ConditionThen(action="ask")
        )]
    ))
    
    # 3. Standort (site selection)
    if not extract_result.sites:
        # No sites defined - ask open question
        questions.append(Question(
            id="site_request",
            question="An welchem Standort möchten Sie arbeiten?",
            type=QuestionType.STRING,
            required=True,
            priority=1,
            group=QuestionGroup.STANDORT
        ))
    elif len(extract_result.sites) == 1:
        # Single site - just confirm
        questions.append(Question(
            id="site_confirmation",
            question=f"Unser Standort ist {extract_result.sites[0].label}. Passt das für Sie?",
            type=QuestionType.BOOLEAN,
            required=True,
            priority=1,
            group=QuestionGroup.STANDORT
        ))
    else:
        # Multiple sites - choice
        questions.append(Question(
            id="site_choice",
            question="An welchem unserer Standorte möchten Sie gerne arbeiten?",
            type=QuestionType.CHOICE,
            options=[site.label for site in extract_result.sites],
            required=True,
            priority=1,
            group=QuestionGroup.STANDORT
        ))
    
    # 4. Einsatzbereich (department)
    if extract_result.all_departments:
        # Check for verbatim question
        verbatim_dept = next(
            (v for v in extract_result.verbatim_candidates 
             if v.is_real_question and re.search(r'fachabteilung|bereich', v.text, re.I)),
            None
        )
        
        dept_question = verbatim_dept.text if verbatim_dept else "In welcher Fachabteilung möchten Sie gerne arbeiten?"
        
        questions.append(Question(
            id="department",
            question=dept_question,
            type=QuestionType.CHOICE,
            options=extract_result.all_departments,
            required=True,
            priority=1,
            group=QuestionGroup.EINSATZBEREICH,
            input_hint="Bitte eine Abteilung nennen."
        ))
    
    # 5. Must-Have Kriterien (Gate Questions)
    for must_have in extract_result.must_have:
        if re.search(r'pflegefach', must_have, re.I):
            questions.append(Question(
                id="qualification_nursing",
                question="Sind Sie examinierte Pflegefachfrau oder Pflegefachmann?",
                type=QuestionType.BOOLEAN,
                required=True,
                priority=1,
                group=QuestionGroup.QUALIFIKATION,
                context=f"Muss-Kriterium: {must_have}"
            ))
        else:
            # Generic must-have question
            slug = _slugify(must_have)
            questions.append(Question(
                id=f"gate_{slug}",
                question=f"Haben Sie: {must_have}?",
                type=QuestionType.BOOLEAN,
                required=True,
                priority=1,
                group=QuestionGroup.QUALIFIKATION,
                context=f"Muss-Kriterium: {must_have}"
            ))
    
    # 6. Alternativen
    for alt in extract_result.alternatives:
        if re.search(r'MFA', alt, re.I):
            questions.append(Question(
                id="op_mfa_alternative",
                question="Wären Sie alternativ für den OP-Bereich mit einer MFA-Qualifizierungsmaßnahme offen?",
                type=QuestionType.BOOLEAN,
                required=False,
                priority=2,
                group=QuestionGroup.QUALIFIKATION
            ))
    
    # 7. Prioritäten als Präferenzfragen
    for prio in extract_result.priorities:
        questions.append(Question(
            id=f"prio_{_slugify(prio.label)}",
            question=f"Haben Sie besonderes Interesse am Bereich {prio.label}?",
            type=QuestionType.BOOLEAN,
            required=False,
            priority=prio.prio_level,
            group=QuestionGroup.PRAEFERENZEN,
            help_text=prio.reason
        ))
    
    # 8. Arbeitszeit (wenn in constraints vorhanden)
    if extract_result.constraints and extract_result.constraints.arbeitszeit:
        vollzeit = extract_result.constraints.arbeitszeit.vollzeit
        teilzeit = extract_result.constraints.arbeitszeit.teilzeit
        
        if vollzeit and teilzeit:
            questions.append(Question(
                id="arbeitszeit",
                question=f"Suchen Sie eine Vollzeit-Stelle ({vollzeit}) oder Teilzeit ({teilzeit})?",
                type=QuestionType.CHOICE,
                options=["Vollzeit", "Teilzeit"],
                required=True,
                priority=2,
                group=QuestionGroup.RAHMEN
            ))
        elif vollzeit:
            questions.append(Question(
                id="vollzeit_confirmation",
                question=f"Die Stelle ist in Vollzeit ({vollzeit}). Ist das für Sie passend?",
                type=QuestionType.BOOLEAN,
                required=True,
                priority=2,
                group=QuestionGroup.RAHMEN
            ))
    
    # 9. Startdatum
    questions.append(Question(
        id="start_date",
        question="Ab wann könnten Sie bei uns anfangen?",
        type=QuestionType.DATE,
        required=True,
        priority=2,
        group=QuestionGroup.RAHMEN
    ))
    
    logger.info(f"Built {len(questions)} base questions")
    
    return questions

