"""
Multi-Stage Extract Pipeline

Parallel extraction using specialized prompts for better coverage and detail.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from ..llm_adapter import call_llm_async
from ..schemas import validate_extract_result
from ..types import ExtractResult
from ...config import get_settings

logger = logging.getLogger(__name__)


async def extract_qualifications(protocol: Dict[str, Any]) -> Dict[str, Any]:
    """Extract qualifications (must-haves, alternatives, deutsch)"""
    settings = get_settings()
    prompt_path = Path(__file__).parent.parent / "prompts" / "extract_qualifications.system.md"
    
    if not prompt_path.exists():
        logger.warning(f"Qualifications prompt not found: {prompt_path}")
        return {"must_have": [], "alternatives": [], "protocol_questions": []}
    
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    logger.info("🔍 Stage 1/3: Extracting qualifications...")
    
    try:
        response = await call_llm_async(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps({"protocol": protocol}, ensure_ascii=False)}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        content = response["choices"][0]["message"]["content"]
        data = json.loads(content)
        
        # Log alle Kategorien
        preferred = data.get('preferred', [])
        alternatives = data.get('alternatives', [])
        must_have = data.get('must_have', [])
        optional = data.get('optional', [])
        
        logger.info(f"  ✓ Found {len(preferred)} preferred, {len(alternatives)} alternatives, "
                   f"{len(must_have)} must-haves, {len(optional)} optional")
        return data
    except Exception as e:
        logger.error(f"Qualifications extraction failed: {e}")
        return {
            "preferred": [],
            "must_have": [], 
            "alternatives": [], 
            "optional": [],
            "protocol_questions": []
        }


async def extract_rahmen(protocol: Dict[str, Any]) -> Dict[str, Any]:
    """Extract rahmenbedingungen (arbeitszeit, gehalt, benefits)"""
    settings = get_settings()
    prompt_path = Path(__file__).parent.parent / "prompts" / "extract_rahmen.system.md"
    
    if not prompt_path.exists():
        logger.warning(f"Rahmen prompt not found: {prompt_path}")
        return {"arbeitszeit": None, "gehalt": None, "benefits": [], "protocol_questions": []}
    
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    logger.info("🔍 Stage 2/3: Extracting rahmenbedingungen...")
    
    try:
        response = await call_llm_async(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps({"protocol": protocol}, ensure_ascii=False)}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        content = response["choices"][0]["message"]["content"]
        data = json.loads(content)
        
        # Debug: Log what we got
        logger.info(f"  ✓ Found arbeitszeit: {bool(data.get('arbeitszeit'))}, gehalt: {bool(data.get('gehalt'))}, benefits: {len(data.get('benefits', []))}")
        logger.debug(f"  📊 Raw rahmen data: {json.dumps(data, ensure_ascii=False)[:200]}...")
        
        return data
    except Exception as e:
        logger.error(f"Rahmen extraction failed: {e}")
        return {"arbeitszeit": None, "gehalt": None, "benefits": [], "protocol_questions": []}


async def extract_info(protocol: Dict[str, Any]) -> Dict[str, Any]:
    """Extract organizational info (sites, departments, priorities)"""
    settings = get_settings()
    prompt_path = Path(__file__).parent.parent / "prompts" / "extract_info.system.md"
    
    if not prompt_path.exists():
        logger.warning(f"Info prompt not found: {prompt_path}")
        return {"sites": [], "all_departments": [], "priorities": [], "roles": [], "protocol_questions": []}
    
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    logger.info("🔍 Stage 3/3: Extracting organizational info...")
    
    try:
        response = await call_llm_async(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps({"protocol": protocol}, ensure_ascii=False)}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        content = response["choices"][0]["message"]["content"]
        data = json.loads(content)
        
        logger.info(f"  ✓ Found {len(data.get('sites', []))} sites, {len(data.get('all_departments', []))} departments")
        return data
    except Exception as e:
        logger.error(f"Info extraction failed: {e}")
        return {"sites": [], "all_departments": [], "priorities": [], "roles": [], "protocol_questions": []}


def merge_protocol_questions(qual_pqs: List, rahmen_pqs: List, info_pqs: List) -> List:
    """Merge protocol questions from all 3 extractors, deduplicate"""
    all_pqs = qual_pqs + rahmen_pqs + info_pqs
    
    # Deduplicate based on text
    seen_texts = set()
    unique_pqs = []
    
    for pq in all_pqs:
        text = pq.get("text", "").lower().strip()
        if text and text not in seen_texts:
            seen_texts.add(text)
            unique_pqs.append(pq)
    
    logger.info(f"  ℹ️  Merged {len(all_pqs)} → {len(unique_pqs)} unique protocol questions")
    return unique_pqs


def merge_constraints(rahmen_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert rahmen extraction to constraints format"""
    constraints = {}
    
    if rahmen_data.get("arbeitszeit"):
        constraints["arbeitszeit"] = rahmen_data["arbeitszeit"]
        logger.debug(f"  → arbeitszeit: {rahmen_data['arbeitszeit']}")
    
    if rahmen_data.get("gehalt"):
        constraints["gehalt"] = rahmen_data["gehalt"]
        logger.info(f"  💰 gehalt extracted: {rahmen_data['gehalt']}")
    else:
        logger.warning("  ⚠️  NO gehalt in rahmen_data!")
    
    if rahmen_data.get("benefits"):
        constraints["benefits"] = rahmen_data["benefits"]
        logger.info(f"  🎁 benefits extracted: {len(rahmen_data['benefits'])} items")
    else:
        logger.warning("  ⚠️  NO benefits in rahmen_data!")
    
    return constraints


async def extract_multi_stage(protocol: Dict[str, Any]) -> ExtractResult:
    """
    Multi-stage extraction with parallel prompts.
    
    Stage 1: Run 3 specialized prompts in parallel
    - Qualifications Extractor
    - Rahmenbedingungen Extractor  
    - Info Extractor
    
    Stage 2: Merge results
    
    Returns:
        ExtractResult with comprehensive data
    """
    logger.info("Starting Multi-Stage Extract Pipeline...")
    
    # STAGE 1: Parallel extraction
    results = await asyncio.gather(
        extract_qualifications(protocol),
        extract_rahmen(protocol),
        extract_info(protocol),
        return_exceptions=True
    )
    
    qual_data, rahmen_data, info_data = results
    
    # Handle exceptions
    if isinstance(qual_data, Exception):
        logger.error(f"Qualifications extraction failed: {qual_data}")
        qual_data = {
            "preferred": [],
            "must_have": [], 
            "alternatives": [], 
            "optional": [],
            "protocol_questions": []
        }
    
    if isinstance(rahmen_data, Exception):
        logger.error(f"Rahmen extraction failed: {rahmen_data}")
        rahmen_data = {"arbeitszeit": None, "gehalt": None, "benefits": [], "protocol_questions": []}
    
    if isinstance(info_data, Exception):
        logger.error(f"Info extraction failed: {info_data}")
        info_data = {"sites": [], "all_departments": [], "priorities": [], "roles": [], "protocol_questions": []}
    
    # STAGE 2: Merge results
    logger.info("📦 Merging results from all extractors...")
    
    merged_data = {
        # From qualifications - NEU: Bevorzugt/Alternativ/Optional unterschieden
        "preferred": qual_data.get("preferred", []),
        "must_have": qual_data.get("must_have", []),
        "alternatives": qual_data.get("alternatives", []),
        "optional_qualifications": qual_data.get("optional", []),
        
        # From info
        "sites": info_data.get("sites", []),
        "all_departments": sorted(set(info_data.get("all_departments", []))),
        "priorities": info_data.get("priorities", []),
        "roles": info_data.get("roles", []),
        "culture_notes": info_data.get("culture_notes", []),
        "department_contacts": info_data.get("department_contacts", {}),
        
        # NEU: Region-Kontext für Standort-Fragen
        "region_context": info_data.get("region_context"),
        "standort_fallback_url": info_data.get("standort_fallback_url"),
        
        # From rahmen
        "constraints": merge_constraints(rahmen_data),
        
        # Merged protocol questions
        "protocol_questions": merge_protocol_questions(
            qual_data.get("protocol_questions", []),
            rahmen_data.get("protocol_questions", []),
            info_data.get("protocol_questions", [])
        ),
        
        # Defaults for optional fields
        "verbatim_candidates": [],
        "motivation_dimensions": [],
        "career_questions_needed": False
    }
    
    # Validate
    validate_extract_result(merged_data)
    
    # Convert to Pydantic model
    extract_result = ExtractResult(**merged_data)
    
    logger.info(
        f"✅ Multi-Stage Extract complete: "
        f"{len(extract_result.must_have)} must-haves, "
        f"{len(extract_result.sites)} sites, "
        f"{len(extract_result.all_departments)} departments, "
        f"{len(extract_result.protocol_questions)} protocol questions"
    )
    
    return extract_result


# Main export - use multi-stage by default
async def extract(protocol: Dict[str, Any]) -> ExtractResult:
    """Main extract function - delegates to multi-stage pipeline"""
    return await extract_multi_stage(protocol)

