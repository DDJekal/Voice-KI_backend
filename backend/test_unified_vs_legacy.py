"""
Test: Unified Pipeline vs. Legacy Pipeline

Vergleicht die neue 3-Prompt Pipeline mit der alten Pipeline
bei der Generierung von Recruiting-Fragebögen.

Usage:
    cd backend
    venv\\Scripts\\python test_unified_vs_legacy.py
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.questions.builder import build_question_catalog


async def test_with_pipeline(protocol_path: Path, use_unified: bool) -> dict:
    """
    Verarbeitet ein Protokoll mit spezifischer Pipeline.
    """
    pipeline_name = "UNIFIED" if use_unified else "LEGACY"
    print(f"\n{'='*60}")
    print(f"Pipeline: {pipeline_name} | Datei: {protocol_path.name}")
    print('='*60)
    
    # Lade Protokoll
    with open(protocol_path, 'r', encoding='utf-8') as f:
        protocol = json.load(f)
    
    # Patche Config
    settings = get_settings()
    original_unified = getattr(settings, 'use_unified_pipeline', False)
    settings.use_unified_pipeline = use_unified
    
    try:
        import time
        start = time.time()
        
        context = {"policy_level": "standard"}
        catalog = await build_question_catalog(protocol, context)
        
        duration = time.time() - start
        
        result = {
            "pipeline": pipeline_name,
            "protocol_file": protocol_path.name,
            "protocol_name": protocol.get('name', 'Unknown'),
            "questions": [q.model_dump() for q in catalog.questions],
            "meta": catalog.meta.model_dump() if catalog.meta else {},
            "_duration": round(duration, 1),
            "_question_count": len(catalog.questions),
            "_generated_at": datetime.now().isoformat()
        }
        
        print(f"  OK {len(catalog.questions)} Fragen in {duration:.1f}s")
        
        # Zeige Fragen-Übersicht
        print(f"\n  Generierte Fragen:")
        for i, q in enumerate(catalog.questions[:8], 1):
            q_text = q.question[:55] + "..." if len(q.question) > 55 else q.question
            print(f"    {i}. [{q.type.value}] {q_text}")
        if len(catalog.questions) > 8:
            print(f"    ... und {len(catalog.questions) - 8} weitere")
        
        return result
        
    except Exception as e:
        print(f"  FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return {
            "pipeline": pipeline_name,
            "protocol_file": protocol_path.name,
            "error": str(e),
            "_generated_at": datetime.now().isoformat()
        }
    
    finally:
        # Restore
        settings.use_unified_pipeline = original_unified


def compare_results(unified: dict, legacy: dict):
    """
    Vergleicht die beiden Pipeline-Ergebnisse.
    """
    print(f"\n{'='*60}")
    print("VERGLEICH")
    print('='*60)
    
    protocol_name = unified.get("protocol_name", "Unknown")
    print(f"\nProtokoll: {protocol_name}")
    
    print(f"\n{'Metrik':<30} {'Legacy':<15} {'Unified':<15}")
    print("-" * 60)
    
    # Question count
    l_count = len(legacy.get("questions", []))
    u_count = len(unified.get("questions", []))
    diff = u_count - l_count
    diff_str = f"({diff:+d})" if diff != 0 else ""
    print(f"{'Anzahl Fragen':<30} {l_count:<15} {u_count:<15} {diff_str}")
    
    # Duration
    l_dur = legacy.get("_duration", 0)
    u_dur = unified.get("_duration", 0)
    print(f"{'Dauer (Sekunden)':<30} {l_dur:.1f}{'':>9} {u_dur:.1f}")
    
    # Preambles
    l_preambles = sum(1 for q in legacy.get("questions", []) if q.get("preamble"))
    u_preambles = sum(1 for q in unified.get("questions", []) if q.get("preamble"))
    print(f"{'Preambles ausgefuellt':<30} {l_preambles:<15} {u_preambles:<15}")
    
    # Errors
    l_err = "Ja" if legacy.get("error") else "Nein"
    u_err = "Ja" if unified.get("error") else "Nein"
    print(f"{'Fehler aufgetreten':<30} {l_err:<15} {u_err:<15}")


async def main():
    """
    Hauptfunktion: Testet alle Protokolle mit beiden Pipelines.
    """
    print("="*60)
    print("    PIPELINE-VERGLEICH: Unified vs. Legacy")
    print("="*60)
    
    # Test-Daten
    test_data_dir = Path(__file__).parent / "test_data"
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    protocol_files = sorted(test_data_dir.glob("*.json"))
    
    if not protocol_files:
        print(f"\nKeine Test-Dateien gefunden in {test_data_dir}")
        sys.exit(1)
    
    print(f"\nGefunden: {len(protocol_files)} Protokolle")
    
    # Teste jedes Protokoll mit beiden Pipelines
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_results = []
    
    for protocol_path in protocol_files:
        print(f"\n\n{'#'*60}")
        print(f"# Test: {protocol_path.name}")
        print(f"{'#'*60}")
        
        # Legacy Pipeline
        legacy_result = await test_with_pipeline(protocol_path, use_unified=False)
        
        # Unified Pipeline
        unified_result = await test_with_pipeline(protocol_path, use_unified=True)
        
        # Vergleiche
        compare_results(unified_result, legacy_result)
        
        # Speichere Ergebnisse
        stem = protocol_path.stem
        
        legacy_path = output_dir / f"legacy_{stem}_{timestamp}.json"
        with open(legacy_path, 'w', encoding='utf-8') as f:
            json.dump(legacy_result, f, ensure_ascii=False, indent=2)
        print(f"\nLegacy Output: {legacy_path.name}")
        
        unified_path = output_dir / f"unified_{stem}_{timestamp}.json"
        with open(unified_path, 'w', encoding='utf-8') as f:
            json.dump(unified_result, f, ensure_ascii=False, indent=2)
        print(f"Unified Output: {unified_path.name}")
        
        all_results.append({
            "protocol": protocol_path.name,
            "legacy": legacy_result,
            "unified": unified_result
        })
    
    # Gesamt-Zusammenfassung
    print(f"\n\n{'='*60}")
    print("GESAMT-ZUSAMMENFASSUNG")
    print('='*60)
    
    for result in all_results:
        protocol = result["protocol"]
        legacy = result["legacy"]
        unified = result["unified"]
        
        l_count = len(legacy.get("questions", []))
        u_count = len(unified.get("questions", []))
        
        print(f"\n{protocol}")
        print(f"  Legacy:  {l_count} Fragen")
        print(f"  Unified: {u_count} Fragen ({u_count - l_count:+d})")
    
    print(f"\n{'='*60}")
    print("TEST ABGESCHLOSSEN")
    print('='*60)


if __name__ == "__main__":
    asyncio.run(main())
