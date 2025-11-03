"""
Expand Conversational Flow Pipeline Stage

Splits questions with conversation_flow into separate sub-questions.
"""

import logging
from typing import List

from ..types import Question

logger = logging.getLogger(__name__)


def expand_conversational_flow(questions: List[Question]) -> List[Question]:
    """
    Expand questions with conversation flows into separate sub-questions.
    
    Currently simplified since we don't generate conversation flows yet.
    
    Args:
        questions: Questions possibly with conversation_flow
        
    Returns:
        Expanded questions
    """
    logger.info(f"Expanding conversational flows for {len(questions)} questions...")
    
    # TODO: Implement expansion logic when conversation_flow is implemented
    # For now, just return as-is
    
    logger.info("Expand stage complete (simplified version)")
    
    return questions

