"""
Question Catalog Builder

Main entry point for question generation pipeline.
Port of src/pipeline/buildCatalog.ts
"""

import logging
from typing import Dict, Any
from datetime import datetime

from .pipeline.extract import extract
from .pipeline.structure import build_questions
from .pipeline.conversational_flow import build_conversational_flow
from .pipeline.expand import expand_conversational_flow
from .pipeline.validate import validate_and_finalize
from .categorizer import categorize_question
from .types import QuestionCatalog, CatalogMeta
from .schemas import validate_question_catalog

logger = logging.getLogger(__name__)


async def build_question_catalog(
    conversation_protocol: Dict[str, Any],
    context: Dict[str, Any] = None
) -> QuestionCatalog:
    """
    Main function: Generates questions.json from conversation protocol.
    
    Pipeline:
    1. Extract (LLM) - Extract structured data from protocol
    2. Structure (deterministic) - Build base questions
    3. Conversational Flow (LLM) - Optimize for voice (simplified)
    4. Expand (deterministic) - Split complex flows (simplified)
    5. Validate (deterministic) - Apply business rules
    6. Categorize (deterministic) - Assign categories
    6.5. Apply Policies (deterministic) - Enhanced conversation intelligence
    
    Args:
        conversation_protocol: Conversation protocol from API
        context: Optional context with policy_level, etc.
        
    Returns:
        QuestionCatalog with all questions
        
    Raises:
        Exception: If any pipeline stage fails
    """
    if context is None:
        context = {}
    
    logger.info("=" * 70)
    logger.info("Starting Question Catalog Builder")
    logger.info("=" * 70)
    
    try:
        # 1. Extract with LLM
        logger.info("Stage 1/6: Extract structured data from protocol...")
        extract_result = await extract(conversation_protocol)
        
        # 2. Build base questions (deterministic)
        logger.info("Stage 2/6: Build base questions...")
        base_questions = build_questions(extract_result)
        
        # 3. Build conversational flows (LLM - simplified for now)
        logger.info("Stage 3/6: Build conversational flows...")
        conversational = await build_conversational_flow(
            base_questions,
            {"priorities": extract_result.priorities}
        )
        
        # 4. Expand flows (simplified for now)
        logger.info("Stage 4/6: Expand conversational flows...")
        expanded = expand_conversational_flow(conversational)
        
        # 5. Validate & finalize
        logger.info("Stage 5/7: Validate and finalize...")
        validation_context = {
            "sites": extract_result.sites,
            "priorities": extract_result.priorities
        }
        validated = validate_and_finalize(expanded, validation_context)
        
        # 6. Categorize
        logger.info("Stage 6/7: Categorize questions...")
        categorized = []
        for q in validated:
            cat = categorize_question(q)
            q.category = cat.category
            q.category_order = cat.order
            categorized.append(q)
        
        # 6.5. Apply Policies (NEU!)
        policy_level = context.get("policy_level")
        audit_log = {"policies_applied": []}
        
        if policy_level:
            logger.info(f"Stage 6.5/7: Apply conversation policies (level: {policy_level})...")
            from .pipeline.policy_resolver import PolicyResolver
            
            policy_resolver = PolicyResolver()
            policy_enhanced, audit_log = policy_resolver.apply_policies(
                categorized,
                policy_level=policy_level
            )
            
            logger.info(f"  Applied {len(audit_log['policies_applied'])} policies")
        else:
            logger.info("Stage 6.5/7: Policies disabled, skipping...")
            policy_enhanced = categorized
        
        # 6.6. Sort questions by category_order, required, priority, and id
        logger.info("Stage 6.6/7: Sort questions by category, required status, and priority...")
        # Sortierung: 
        # 1. category_order (niedrigere Nummer = früher)
        # 2. required (True = früher als False)
        # 3. priority (niedrigere Nummer = wichtiger)
        # 4. id (alphabetisch für Konsistenz)
        policy_enhanced.sort(key=lambda q: (q.category_order, not q.required, q.priority, q.id))
        logger.info(f"  Sorted {len(policy_enhanced)} questions")
        
        # 7. Wrap with metadata
        catalog = QuestionCatalog(
            meta=CatalogMeta(
                schema_version="1.0",
                generated_at=datetime.now().isoformat(),
                generator="voiceki-python-question-builder@1.0.0",
                policies_applied=audit_log.get("policies_applied") if policy_level else None
            ),
            questions=policy_enhanced
        )
        
        # 8. Validate catalog
        # Use by_alias=True to serialize with "_meta" for backward compatibility
        validate_question_catalog(catalog.model_dump(by_alias=True))
        
        logger.info("=" * 70)
        logger.info(f"✅ Question Catalog Built Successfully!")
        logger.info(f"   Total Questions: {len(catalog.questions)}")
        logger.info(f"   Required: {sum(1 for q in catalog.questions if q.required)}")
        logger.info(f"   Optional: {sum(1 for q in catalog.questions if not q.required)}")
        
        # Policy stats
        if policy_level and audit_log.get("policies_applied"):
            logger.info(f"   Policies Applied: {len(audit_log['policies_applied'])}")
            
            # Count questions with enhancements
            with_slots = sum(1 for q in catalog.questions if q.slot_config)
            with_hints = sum(1 for q in catalog.questions if q.conversation_hints)
            logger.info(f"   Questions with Slot-Config: {with_slots}")
            logger.info(f"   Questions with Conversation-Hints: {with_hints}")
        
        # Group by category
        categories = {}
        for q in catalog.questions:
            cat = q.category or "uncategorized"
            categories[cat] = categories.get(cat, 0) + 1
        
        logger.info("   Categories:")
        for cat, count in sorted(categories.items()):
            logger.info(f"     - {cat}: {count}")
        
        logger.info("=" * 70)
        
        return catalog
        
    except Exception as e:
        logger.error(f"❌ Question Catalog Builder failed: {e}")
        raise

