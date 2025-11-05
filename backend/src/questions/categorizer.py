"""
Question Categorizer

Categorizes questions based on content and context.
Port of src/categorization/categorizer.ts
"""

import logging
from dataclasses import dataclass

from .types import Question

logger = logging.getLogger(__name__)


@dataclass
class CategoryMapping:
    """Category mapping for a question"""
    category: str
    order: int
    description: str


def categorize_question(question: Question, page_name: str = "") -> CategoryMapping:
    """
    Categorize question based on content and context.
    
    Args:
        question: Question to categorize
        page_name: Optional page name for additional context
        
    Returns:
        CategoryMapping with category, order, description
    """
    q_lower = question.question.lower()
    page_lower = page_name.lower()
    
    # 1. Identifikation (confirmation questions) - ERSTE Kategorie
    if "spreche ich mit" in q_lower or ("adresse" in q_lower and "korrekt" in q_lower):
        return CategoryMapping(
            category="identifikation",
            order=1,
            description="Identifikation & Bestätigung"
        )
    
    # 2. Kontaktinformationen (data collection)
    if ("adresse" in q_lower and "korrekt" not in q_lower) or "telefon" in q_lower or "erreichbar" in q_lower or "e-mail" in q_lower:
        return CategoryMapping(
            category="kontaktinformationen",
            order=2,
            description="Kontaktdaten"
        )
    
    # 3. Gate Questions & Must-Have Qualifikationen - HÖCHSTE PRIORITÄT!
    # Prüfe zuerst ob es ein Must-Have Kriterium ist (aus context)
    is_gate = False
    if question.context and "muss-kriterium" in question.context.lower():
        is_gate = True
    
    # Oder prüfe Keywords für Gate Questions
    gate_keywords = [
        "zwingend", "pflicht", "examen", "qualifikation", "pflegefach",
        "fachweiterbildung", "weiterbildung", "ausbildung", "abschluss",
        "zertifikat", "berechtigung", "erlaubnis", "befähigung"
    ]
    
    if question.required and (is_gate or any(kw in q_lower for kw in gate_keywords)):
        return CategoryMapping(
            category="standardqualifikationen",
            order=1,  # HÖCHSTE PRIORITÄT (war vorher 3)
            description="Qualifikationen & Must-Have Kriterien (Gate)"
        )
    
    # 4. Rahmenbedingungen (basics wie Arbeitszeit, Startdatum)
    if (page_lower and "rahmenbedingungen" in page_lower) or \
       any(kw in q_lower for kw in ["arbeitszeit", "schicht", "vollzeit", "teilzeit", "anfangen", "startdatum", "verfügbar"]):
        return CategoryMapping(
            category="rahmenbedingungen",
            order=2,  # War vorher 4
            description="Rahmenbedingungen"
        )
    
    # 5. Standort
    if "standort" in q_lower or "einsatzort" in q_lower:
        return CategoryMapping(
            category="standort",
            order=3,  # War vorher 5
            description="Standorte"
        )
    
    # 6. Einsatzbereiche
    if "abteilung" in q_lower or "bereich" in q_lower or "station" in q_lower or "fachabteilung" in q_lower:
        return CategoryMapping(
            category="einsatzbereiche",
            order=4,  # War vorher 6
            description="Einsatzbereiche & Abteilungen"
        )
    
    # 7. Präferenzen
    if "interesse" in q_lower or "präferenz" in q_lower or "wünschen" in q_lower:
        return CategoryMapping(
            category="praeferenzen",
            order=5,  # War vorher 7
            description="Präferenzen"
        )
    
    # 8. Default: Zusätzliche Informationen
    return CategoryMapping(
        category="zusaetzliche_informationen",
        order=6,  # War vorher 8
        description="Zusätzliche Informationen"
    )

