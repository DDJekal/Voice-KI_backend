"""
Unified Question Generation Pipeline

Neue vereinfachte Pipeline mit 3 spezialisierten Prompts:
1. Kriterien → Anforderungs-Fragen
2. Rahmenbedingungen → Arbeitszeit-Fragen + Info-Pool
3. Weitere Informationen → Standort/Bereichs-Fragen + Kontext

Vorteile:
- Konsolidierte, natürliche Fragen
- Weniger Fragen insgesamt (5-8 statt 10+)
- Bedingte Logik
- Info-Pool für KI-Kontext
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from ..llm_adapter import call_llm_async
from ..types import Question, QuestionType, QuestionGroup, QuestionCatalog, CatalogMeta

logger = logging.getLogger(__name__)


async def generate_from_kriterien(protocol: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generiert Fragen aus "Bewerber erfüllt folgende Kriterien" Seite.
    """
    logger.info("🔍 Generiere Fragen aus Kriterien-Seite...")
    
    # Finde Kriterien-Seite
    kriterien_page = None
    for page in protocol.get('pages', []):
        if 'kriterien' in page.get('name', '').lower():
            kriterien_page = page
            break
    
    if not kriterien_page:
        logger.warning("  Keine Kriterien-Seite gefunden")
        return {"questions": [], "info_pool": {}}
    
    # Lade Prompt
    prompt_path = Path(__file__).parent.parent / "prompts" / "generate_kriterien.system.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    # LLM Call
    response = await call_llm_async(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(kriterien_page, ensure_ascii=False)}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    content = response["choices"][0]["message"]["content"]
    result = json.loads(content)
    
    logger.info(f"  ✓ {len(result.get('questions', []))} Fragen aus Kriterien generiert")
    return result


async def generate_from_rahmen(protocol: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generiert Fragen aus "Bewerber akzeptiert folgende Rahmenbedingungen" Seite.
    """
    logger.info("🔍 Generiere Fragen aus Rahmenbedingungen-Seite...")
    
    # Finde Rahmen-Seite
    rahmen_page = None
    for page in protocol.get('pages', []):
        if 'rahmenbedingungen' in page.get('name', '').lower() or 'akzeptiert' in page.get('name', '').lower():
            rahmen_page = page
            break
    
    if not rahmen_page:
        logger.warning("  Keine Rahmenbedingungen-Seite gefunden")
        return {"questions": [], "info_pool": {}}
    
    # Lade Prompt
    prompt_path = Path(__file__).parent.parent / "prompts" / "generate_rahmen.system.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    # LLM Call
    response = await call_llm_async(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(rahmen_page, ensure_ascii=False)}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    content = response["choices"][0]["message"]["content"]
    result = json.loads(content)
    
    logger.info(f"  ✓ {len(result.get('questions', []))} Fragen aus Rahmen generiert")
    return result


async def generate_from_infos(protocol: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generiert Fragen aus "Weitere Informationen" Seite.
    """
    logger.info("🔍 Generiere Fragen aus Weitere-Informationen-Seite...")
    
    # Finde Info-Seite
    info_page = None
    for page in protocol.get('pages', []):
        if 'weitere' in page.get('name', '').lower() or 'informationen' in page.get('name', '').lower():
            info_page = page
            break
    
    if not info_page:
        logger.warning("  Keine Weitere-Informationen-Seite gefunden")
        return {"questions": [], "info_pool": {}}
    
    # Lade Prompt
    prompt_path = Path(__file__).parent.parent / "prompts" / "generate_infos.system.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    # LLM Call
    response = await call_llm_async(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(info_page, ensure_ascii=False)}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    content = response["choices"][0]["message"]["content"]
    result = json.loads(content)
    
    logger.info(f"  ✓ {len(result.get('questions', []))} Fragen aus Infos generiert")
    return result


def merge_results(kriterien: Dict, rahmen: Dict, infos: Dict) -> tuple:
    """
    Merged die Ergebnisse der 3 Prompts zu einer sortierten Fragenliste + Knowledge-Base.
    
    Returns:
        tuple: (List[Question], Dict knowledge_base)
    """
    logger.info("📦 Merge Ergebnisse von 3 Prompts...")
    
    all_questions = []
    
    # Sammle alle Fragen
    for source, name in [(kriterien, "Kriterien"), (rahmen, "Rahmen"), (infos, "Infos")]:
        questions = source.get('questions', [])
        logger.info(f"  {name}: {len(questions)} Fragen")
        all_questions.extend(questions)
    
    # Merge Knowledge-Base aus allen 3 Prompts (NICHT pro Frage duplizieren!)
    rahmen_pool = rahmen.get('info_pool', {})
    infos_pool = infos.get('info_pool', {})
    
    knowledge_base = {
        # Aus Rahmenbedingungen
        "salary_info": rahmen_pool.get('salary_info', {}),
        "work_conditions": rahmen_pool.get('work_conditions', []),
        "benefits": rahmen_pool.get('benefits', []),
        
        # Aus Weitere Informationen
        "standort": infos_pool.get('standort', {}),
        "company_culture": infos_pool.get('company_culture', []),
        "company_benefits": infos_pool.get('company_benefits', []),
        "location_priorities": infos_pool.get('location_priorities', []),
        "internal_notes": infos_pool.get('internal_notes', []),
        "general_info": infos_pool.get('general_info', [])
    }
    
    # Merge benefits (aus beiden Quellen)
    all_benefits = knowledge_base.get('benefits', []) + knowledge_base.get('company_benefits', [])
    knowledge_base['company_benefits'] = all_benefits
    del knowledge_base['benefits']
    
    logger.info(f"  Knowledge-Base: {sum(1 for v in knowledge_base.values() if v)} Kategorien gefuellt")
    
    # Sortiere Fragen
    def sort_key(q: dict) -> tuple:
        # Phase 2 vor Phase 4
        phase = q.get('phase', 4)
        # Bereichs-Frage zuerst (wenn vorhanden)
        if q.get('id') == 'bereich':
            return (0, 0, '')
        # Dann nach Phase, priority und id
        priority = q.get('priority', 2)
        return (phase, priority, q.get('id', ''))
    
    all_questions.sort(key=sort_key)
    
    # Gültige QuestionGroup Werte
    valid_groups = {
        "Motivation", "Standort", "Einsatzbereich", "Qualifikation",
        "Präferenzen", "Rahmen", "Werdegang", "Verfügbarkeit", "Kontakt"
    }
    
    # Konvertiere zu Question-Objekten
    question_objects = []
    for q_dict in all_questions:
        try:
            # Validiere und korrigiere group
            group = q_dict.get('group')
            if group and group not in valid_groups:
                logger.warning(f"  Invalid group '{group}', mapping to 'Qualifikation'")
                q_dict['group'] = "Qualifikation"
            
            # Konvertiere zu Question
            question = Question(**q_dict)
            question_objects.append(question)
        except Exception as e:
            logger.warning(f"  Skipping invalid question: {e}")
            continue
    
    logger.info(f"  ✓ Merged: {len(question_objects)} finale Fragen")
    return question_objects, knowledge_base


async def generate_unified(protocol: Dict[str, Any]) -> QuestionCatalog:
    """
    Haupt-Funktion: Generiert Fragen mit 3 spezialisierten Prompts.
    
    Args:
        protocol: Das vollständige Gesprächsprotokoll
        
    Returns:
        QuestionCatalog mit konsolidierten Fragen
    """
    logger.info("🚀 Starte Unified Question Generation (3 Prompts)...")
    
    try:
        # Rufe alle 3 Prompts parallel auf
        results = await asyncio.gather(
            generate_from_kriterien(protocol),
            generate_from_rahmen(protocol),
            generate_from_infos(protocol),
            return_exceptions=True
        )
        
        kriterien_result, rahmen_result, infos_result = results
        
        # Handle exceptions
        if isinstance(kriterien_result, Exception):
            logger.error(f"Kriterien-Generierung fehlgeschlagen: {kriterien_result}")
            kriterien_result = {"questions": [], "info_pool": {}}
        
        if isinstance(rahmen_result, Exception):
            logger.error(f"Rahmen-Generierung fehlgeschlagen: {rahmen_result}")
            rahmen_result = {"questions": [], "info_pool": {}}
        
        if isinstance(infos_result, Exception):
            logger.error(f"Infos-Generierung fehlgeschlagen: {infos_result}")
            infos_result = {"questions": [], "info_pool": {}}
        
        # Merge Ergebnisse
        questions, knowledge_base = merge_results(kriterien_result, rahmen_result, infos_result)
        
        # Erstelle Catalog
        catalog = QuestionCatalog(
            questions=questions,
            meta=CatalogMeta(
                policies_applied=[
                    f"unified_pipeline_3_prompts",
                    f"total_questions: {len(questions)}"
                ]
            )
        )
        
        # Knowledge-Base als Attribut speichern (für Export)
        object.__setattr__(catalog, 'knowledge_base', knowledge_base)
        
        logger.info(f"✅ Unified Generation complete: {len(questions)} Fragen, KB mit {len(knowledge_base)} Kategorien")
        return catalog
        
    except Exception as e:
        logger.error(f"❌ Unified Generation failed: {e}")
        raise
