"""
JSON Schema validation for Question Generator

Port of TypeScript Ajv schemas to Python jsonschema.
"""

from jsonschema import validate, ValidationError
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


# Extract Result Schema (port of EXTRACT_SCHEMA from extract.schema.ts)
EXTRACT_RESULT_SCHEMA = {
    "type": "object",
    "required": ["sites", "priorities", "must_have", "all_departments"],
    "properties": {
        "sites": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["label", "stations"],
                "properties": {
                    "label": {"type": "string"},
                    "stations": {"type": "array", "items": {"type": "string"}},
                    "source": {
                        "type": "object",
                        "properties": {"page_id": {"type": "integer"}},
                        "additionalProperties": True
                    }
                }
            }
        },
        "roles": {
            "type": "array",
            "items": {"type": "string"}
        },
        "priorities": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["label", "reason"],
                "properties": {
                    "label": {"type": "string"},
                    "reason": {"type": "string"},
                    "prio_level": {"enum": [1, 2, 3]},
                    "source": {
                        "type": "object",
                        "properties": {
                            "page_id": {"type": "integer"},
                            "prompt_id": {"type": "integer"}
                        },
                        "additionalProperties": True
                    }
                }
            }
        },
        "must_have": {"type": "array", "items": {"type": "string"}},
        "alternatives": {"type": "array", "items": {"type": "string"}},
        "constraints": {
            "type": "object",
            "properties": {
                "arbeitszeit": {
                    "type": "object",
                    "properties": {
                        "vollzeit": {"type": "string"},
                        "teilzeit": {"type": "string"}
                    }
                },
                "tarif": {"type": "string"},
                "schichten": {"type": "string"}
            }
        },
        "verbatim_candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["text", "page_id"],
                "properties": {
                    "text": {"type": "string"},
                    "page_id": {"type": "integer"},
                    "prompt_id": {"type": "integer"},
                    "is_real_question": {"type": "boolean"}
                },
                "additionalProperties": True
            }
        },
        "all_departments": {"type": "array", "items": {"type": "string"}}
    },
    "additionalProperties": True
}


# Question Catalog Schema
QUESTION_CATALOG_SCHEMA = {
    "type": "object",
    "required": ["_meta", "questions"],
    "properties": {
        "_meta": {
            "type": "object",
            "required": ["schema_version", "generated_at", "generator"],
            "properties": {
                "schema_version": {"type": "string"},
                "generated_at": {"type": "string"},
                "generator": {"type": "string"},
                "policies_applied": {"type": "array", "items": {"type": "string"}}
            }
        },
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "question", "type", "required", "priority"],
                "properties": {
                    "id": {"type": "string"},
                    "question": {"type": "string"},
                    "type": {
                        "enum": ["string", "date", "boolean", "choice", "multi_choice", "ranked_list"]
                    },
                    "options": {"type": "array", "items": {"type": "string"}},
                    "conversation_flow": {"type": "object"},
                    "required": {"type": "boolean"},
                    "priority": {"enum": [1, 2, 3]},
                    "group": {"type": "string"},
                    "help_text": {"type": "string"},
                    "input_hint": {"type": "string"},
                    "conditions": {"type": "array"},
                    "source": {"type": "object"},
                    "context": {"type": "string"},
                    "category": {"type": "string"},
                    "category_order": {"type": "integer"},
                    # Policy enhancements
                    "slot_config": {
                        "type": "object",
                        "properties": {
                            "fills_slot": {"type": "string"},
                            "required": {"type": "boolean"},
                            "confidence_threshold": {"type": "number"},
                            "validation": {"type": "object"}
                        }
                    },
                    "gate_config": {
                        "type": "object",
                        "properties": {
                            "is_gate": {"type": "boolean"},
                            "is_alternative": {"type": "boolean"},
                            "alternative_for": {"type": "string"},
                            "can_satisfy_gate": {"type": "boolean"},
                            "final_alternative": {"type": "boolean"},
                            "end_message_if_all_no": {"type": "string"},
                            "requires_slots": {"type": "array", "items": {"type": "string"}},
                            "condition": {"type": "string"},
                            "context_triggers": {"type": "object"}
                        }
                    },
                    "conversation_hints": {
                        "type": "object",
                        "properties": {
                            "on_unclear_answer": {"type": "string"},
                            "on_negative_answer": {"type": "string"},
                            "confidence_boost_phrases": {"type": "array", "items": {"type": "string"}},
                            "diversify_after": {"type": "string"}
                        }
                    }
                }
            }
        }
    }
}


def validate_extract_result(data: Dict[str, Any]) -> None:
    """
    Validate extract result against schema.
    
    Args:
        data: Extract result data to validate
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        validate(instance=data, schema=EXTRACT_RESULT_SCHEMA)
        logger.info("Extract result validation successful")
    except ValidationError as e:
        logger.error(f"Extract result validation failed: {e.message}")
        raise


def validate_question_catalog(data: Dict[str, Any]) -> None:
    """
    Validate question catalog against schema.
    
    Args:
        data: Question catalog data to validate
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        validate(instance=data, schema=QUESTION_CATALOG_SCHEMA)
        logger.info(f"Question catalog validation successful ({len(data.get('questions', []))} questions)")
    except ValidationError as e:
        logger.error(f"Question catalog validation failed: {e.message}")
        raise

