"""
Validate Pipeline Stage

Rule-based validation and finalization of questions.
"""

import logging
from typing import List, Dict, Any

from ..types import Question

logger = logging.getLogger(__name__)


def validate_and_finalize(
    questions: List[Question],
    context: Dict[str, Any]
) -> List[Question]:
    """
    Apply business rules and validate questions.
    
    Args:
        questions: Questions to validate
        context: Context with sites, priorities, candidate data
        
    Returns:
        Validated and finalized questions
    """
    logger.info(f"Validating and finalizing {len(questions)} questions...")
    
    finalized = []
    
    for question in questions:
        # Apply business rules
        
        # 1. Add priority help text to department question
        if question.id == "department" and context.get("priorities"):
            priorities = context["priorities"]
            prio_1 = [p.label for p in priorities if p.prio_level == 1]
            if prio_1:
                question.help_text = f"Aktuell besonders gesucht: {', '.join(prio_1)}"
        
        # 2. Validate IDs are unique
        if any(q.id == question.id for q in finalized):
            logger.warning(f"Duplicate question ID: {question.id}")
        
        finalized.append(question)
    
    logger.info(f"Validation complete: {len(finalized)} questions finalized")
    
    return finalized

