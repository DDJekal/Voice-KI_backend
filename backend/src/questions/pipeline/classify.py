"""
STAGE 0: Intent Classification Pipeline

Klassifiziert Protokoll-Items nach ihrem Intent, bevor sie verarbeitet werden.
Dies verhindert, dass Informationen verloren gehen oder falsch kategorisiert werden.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from ..openai_adapter import call_openai_async

logger = logging.getLogger(__name__)


async def classify_protocol_items(protocol: Dict[str, Any]) -> Dict[str, List]:
    """
    Klassifiziert alle Items im Protokoll nach Intent.
    
    Args:
        protocol: Das vollständige Gesprächsprotokoll
        
    Returns:
        {
            'gate_items': [...],            # Muss-Kriterien
            'preference_items': [...],       # Präferenz-Fragen
            'information_items': [...],      # Info für Kandidat
            'internal_notes': [...],         # Recruiter-Notizen
            'blacklist': [...],              # Ausschluss-Kriterien
            'priorities': [...],             # Priorisierungen
            'metadata': [...],               # System-Felder
            'alternative_qualifications': [...] # Alternative Qualifikationen
        }
    """
    logger.info("🔍 Starting Intent Classification...")
    
    # 1. Sammle alle Protokoll-Items
    all_items = _collect_protocol_items(protocol)
    logger.info(f"  Collected {len(all_items)} protocol items")
    
    if not all_items:
        logger.warning("  No items to classify - returning empty structure")
        return _empty_classification()
    
    # 2. Lade Classification Prompt
    prompt_path = Path(__file__).parent.parent / "prompts" / "extract_classify.system.md"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    
    # 3. Baue User Message mit allen Items
    user_message = _build_classification_message(protocol, all_items)
    
    # 4. LLM Call
    logger.info("  Calling LLM for classification...")
    from ...config import get_settings
    settings = get_settings()
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    response = await call_openai_async(
        model=settings.openai_model,
        temperature=0.3,  # Niedrig für konsistente Klassifizierung
        messages=messages,
        response_format={"type": "json_object"}
    )
    
    # 5. Parse Response
    try:
        # Extract content from OpenAI response
        content = response['choices'][0]['message']['content']
        classification_result = json.loads(content)
        logger.info("  ✓ Classification successful")
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"  ✗ Failed to parse classification response: {e}")
        logger.debug(f"  Response was: {str(response)[:500]}")
        return _empty_classification()
    
    # 6. Segment nach Intent
    segmented = _segment_by_intent(classification_result, all_items)
    
    # 7. Log Results
    logger.info(f"  Segmented items:")
    logger.info(f"    - Gate Items: {len(segmented['gate_items'])}")
    logger.info(f"    - Preference Items: {len(segmented['preference_items'])}")
    logger.info(f"    - Information Items: {len(segmented['information_items'])}")
    logger.info(f"    - Internal Notes: {len(segmented['internal_notes'])}")
    logger.info(f"    - Blacklist: {len(segmented['blacklist'])}")
    logger.info(f"    - Priorities: {len(segmented['priorities'])}")
    logger.info(f"    - Metadata: {len(segmented['metadata'])}")
    logger.info(f"    - Alternative Qualifications: {len(segmented['alternative_qualifications'])}")
    
    return segmented


def _collect_protocol_items(protocol: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Sammelt alle Items aus dem Protokoll mit Metadaten.
    
    Returns:
        [
            {
                'id': 'page_1_prompt_1',
                'text': 'zwingend: Deutschkenntnisse B2',
                'page_name': 'Der Bewerber erfüllt folgende Kriterien:',
                'position': 1
            },
            ...
        ]
    """
    items = []
    
    pages = protocol.get('pages', [])
    for page in pages:
        page_name = page.get('name', 'Unnamed Page')
        prompts = page.get('prompts', [])
        
        for prompt in prompts:
            items.append({
                'id': f"page_{page.get('id', 'unknown')}_prompt_{prompt.get('id', 'unknown')}",
                'text': prompt.get('question', ''),
                'page_name': page_name,
                'position': prompt.get('position', 0),
                'page_id': page.get('id'),
                'prompt_id': prompt.get('id')
            })
    
    return items


def _build_classification_message(protocol: Dict[str, Any], items: List[Dict]) -> str:
    """
    Baut die User Message für LLM Classification.
    """
    protocol_name = protocol.get('name', 'Unbekanntes Protokoll')
    
    message = f"""# Protokoll: {protocol_name}

Klassifiziere folgende Items nach Intent:

"""
    
    for i, item in enumerate(items, 1):
        message += f"{i}. [{item['page_name']}] {item['text']}\n"
    
    message += """

Gebe ein JSON-Objekt zurück mit "classified_items" als Key und einem Dictionary mit item_id -> classification.
"""
    
    return message


def _segment_by_intent(classification_result: Dict, all_items: List[Dict]) -> Dict[str, List]:
    """
    Segmentiert klassifizierte Items nach Intent.
    """
    segmented = _empty_classification()
    
    classified_items = classification_result.get('classified_items', {})
    
    # Mapping: item_index (1-based) -> item data
    item_by_index = {str(i+1): item for i, item in enumerate(all_items)}
    
    for item_key, classification in classified_items.items():
        intent = classification.get('intent', 'INFORMATION').upper()
        original_text = classification.get('original_text', '')
        
        # Finde das Original Item
        item_data = None
        if item_key.startswith('item_'):
            idx = item_key.replace('item_', '')
            item_data = item_by_index.get(idx)
        
        if not item_data:
            logger.warning(f"Could not find item for key: {item_key}")
            continue
        
        # Erstelle strukturiertes Item
        structured_item = {
            'text': original_text or item_data['text'],
            'page_name': item_data.get('page_name'),
            'position': item_data.get('position'),
            'confidence': classification.get('confidence', 'unknown'),
            'reason': classification.get('reason', '')
        }
        
        # Zuordnung nach Intent
        if intent == 'GATE_QUESTION':
            segmented['gate_items'].append(structured_item)
        elif intent == 'PREFERENCE_QUESTION':
            segmented['preference_items'].append(structured_item)
        elif intent == 'INFORMATION':
            segmented['information_items'].append(structured_item)
        elif intent == 'INTERNAL_NOTE':
            segmented['internal_notes'].append(structured_item)
        elif intent == 'BLACKLIST':
            segmented['blacklist'].append(structured_item)
        elif intent == 'PRIORITY':
            segmented['priorities'].append(structured_item)
        elif intent == 'METADATA':
            segmented['metadata'].append(structured_item)
        elif intent == 'ALTERNATIVE_QUALIFICATION':
            segmented['alternative_qualifications'].append(structured_item)
        else:
            logger.warning(f"Unknown intent: {intent}, treating as INFORMATION")
            segmented['information_items'].append(structured_item)
    
    return segmented


def _empty_classification() -> Dict[str, List]:
    """
    Returns empty classification structure.
    """
    return {
        'gate_items': [],
        'preference_items': [],
        'information_items': [],
        'internal_notes': [],
        'blacklist': [],
        'priorities': [],
        'metadata': [],
        'alternative_qualifications': []
    }

