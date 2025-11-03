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
    
    # 1. Standardqualifikationen (Gate Questions) - check first!
    if (question.required and
        any(kw in q_lower for kw in ["zwingend", "pflicht", "examen", "qualifikation", "pflegefach"])):
        return CategoryMapping(
            category="standardqualifikationen",
            order=3,
            description="Standardqualifikationen (Gate)"
        )
    
    # 2. Identifikation (confirmation questions)
    if "spreche ich mit" in q_lower or ("adresse" in q_lower and "korrekt" in q_lower):
        return CategoryMapping(
            category="identifikation",
            order=1,
            description="Identifikation & Bestätigung"
        )
    
    # 3. Kontaktinformationen (data collection)
    if ("adresse" in q_lower and "korrekt" not in q_lower) or "telefon" in q_lower or "erreichbar" in q_lower or "e-mail" in q_lower:
        return CategoryMapping(
            category="kontaktinformationen",
            order=2,
            description="Kontaktdaten"
        )
    
    # 4. Standort
    if "standort" in q_lower or "einsatzort" in q_lower:
        return CategoryMapping(
            category="standort",
            order=5,
            description="Standorte"
        )
    
    # 5. Einsatzbereiche
    if "abteilung" in q_lower or "bereich" in q_lower or "station" in q_lower or "fachabteilung" in q_lower:
        return CategoryMapping(
            category="einsatzbereiche",
            order=6,
            description="Einsatzbereiche & Abteilungen"
        )
    
    # 6. Rahmenbedingungen
    if (page_lower and "rahmenbedingungen" in page_lower) or \
       any(kw in q_lower for kw in ["arbeitszeit", "schicht", "urlaub", "vollzeit", "teilzeit", "vergütung", "anfangen"]):
        return CategoryMapping(
            category="rahmenbedingungen",
            order=7,
            description="Rahmenbedingungen"
        )
    
    # 7. Präferenzen
    if "interesse" in q_lower or "präferenz" in q_lower or "wünschen" in q_lower:
        return CategoryMapping(
            category="praeferenzen",
            order=8,
            description="Präferenzen"
        )
    
    # 8. Default: Zusätzliche Informationen
    return CategoryMapping(
        category="zusaetzliche_informationen",
        order=9,
        description="Zusätzliche Informationen"
    )

