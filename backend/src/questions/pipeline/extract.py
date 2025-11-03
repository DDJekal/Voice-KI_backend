"""
Extract Pipeline Stage

LLM-based extraction of structured data from conversation protocol.
Port of src/pipeline/extract.ts
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

from ..openai_adapter import call_openai_async
from ..schemas import validate_extract_result
from ..types import ExtractResult
from ...config import get_settings

logger = logging.getLogger(__name__)


async def extract(protocol: Dict[str, Any]) -> ExtractResult:
    """
    Extract structured information from conversation protocol using LLM.
    
    This is the first pipeline stage that analyzes the raw protocol
    and extracts:
    - Sites and stations
    - Priorities
    - Must-have criteria
    - Alternatives
    - Constraints
    - Verbatim question candidates
    - All departments
    
    Args:
        protocol: Conversation protocol from API
        
    Returns:
        ExtractResult with structured data
        
    Raises:
        Exception: If LLM call fails or validation fails
    """
    settings = get_settings()
    
    # Load system prompt
    prompt_path = Path(__file__).parent.parent / "prompts" / "extract.system.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Extract prompt not found: {prompt_path}")
    
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    logger.info("Starting extract pipeline stage...")
    
    # Call OpenAI
    response = await call_openai_async(
        model=settings.openai_model,
        temperature=1.0,  # Higher temperature for creativity
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({"protocol": protocol}, ensure_ascii=False)}
        ],
        response_format={"type": "json_object"}
    )
    
    # Parse response
    content = response["choices"][0]["message"]["content"]
    
    if not content:
        raise ValueError("LLM returned no content")
    
    data = json.loads(content)
    
    # Validate against schema
    validate_extract_result(data)
    
    # Post-process: dedupe & sort departments
    if "all_departments" in data:
        data["all_departments"] = sorted(set(data.get("all_departments", [])))
    
    # Convert to Pydantic model
    extract_result = ExtractResult(**data)
    
    logger.info(
        f"Extract complete: "
        f"{len(extract_result.sites)} sites, "
        f"{len(extract_result.priorities)} priorities, "
        f"{len(extract_result.all_departments)} departments"
    )
    
    return extract_result

