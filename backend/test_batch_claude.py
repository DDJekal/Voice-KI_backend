"""
Batch Test: Claude Fragengenerierung für alle Test-Protokolle

Verarbeitet alle JSON-Dateien im test_data Ordner und speichert
die generierten Fragebögen im test_output Ordner.

Usage:
    cd backend
    venv\\Scripts\\python test_batch_claude.py
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


async def process_protocol(protocol_path: Path, output_dir: Path) -> dict:
    """
    Verarbeitet ein einzelnes Protokoll mit Claude.
    """
    print(f"\n{'='*60}")
    print(f"VERARBEITE: {protocol_path.name}")
    print('='*60)
    
    # Lade Protokoll
    with open(protocol_path, 'r', encoding='utf-8') as f:
        protocol = json.load(f)
    
    protocol_name = protocol.get('name', protocol_path.stem)
    print(f"  Name: {protocol_name}")
    print(f"  Seiten: {len(protocol.get('pages', []))}")
    
    try:
        import time
        start = time.time()
        
        context = {"policy_level": "standard"}
        catalog = await build_question_catalog(protocol, context)
        
        duration = time.time() - start
        
        # Erstelle Output
        result = {
            "protocol_file": protocol_path.name,
            "protocol_name": protocol_name,
            "questions": [q.model_dump() for q in catalog.questions],
            "meta": catalog.meta.model_dump() if catalog.meta else {},
            "_generated_at": datetime.now().isoformat(),
            "_duration_seconds": round(duration, 1),
            "_question_count": len(catalog.questions)
        }
        
        # Speichere Output
        output_filename = f"claude_{protocol_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"  OK Generiert: {len(catalog.questions)} Fragen")
        print(f"  OK Dauer: {duration:.1f}s")
        print(f"  OK Gespeichert: {output_filename}")
        
        # Zeige Fragen-Übersicht
        print(f"\n  Fragen-Übersicht:")
        for i, q in enumerate(catalog.questions[:5], 1):
            q_text = q.question[:50] + "..." if len(q.question) > 50 else q.question
            print(f"    {i}. [{q.type.value}] {q_text}")
        if len(catalog.questions) > 5:
            print(f"    ... und {len(catalog.questions) - 5} weitere")
        
        return result
        
    except Exception as e:
        print(f"  FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return {
            "protocol_file": protocol_path.name,
            "error": str(e),
            "_generated_at": datetime.now().isoformat()
        }


async def main():
    """
    Hauptfunktion: Verarbeitet alle Test-Protokolle.
    """
    print("="*60)
    print("    BATCH TEST: Claude Fragengenerierung")
    print("="*60)
    
    # Pfade
    test_data_dir = Path(__file__).parent / "test_data"
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    # Finde alle JSON-Dateien
    protocol_files = sorted(test_data_dir.glob("*.json"))
    
    if not protocol_files:
        print(f"\nKeine JSON-Dateien in {test_data_dir} gefunden!")
        sys.exit(1)
    
    print(f"\nGefunden: {len(protocol_files)} Protokolle")
    for pf in protocol_files:
        print(f"  - {pf.name}")
    
    # Check API Key
    settings = get_settings()
    print(f"\nClaude Model: {settings.anthropic_model}")
    print(f"API Key: {'Vorhanden' if settings.anthropic_api_key else 'FEHLT!'}")
    
    if not settings.anthropic_api_key:
        print("\nFEHLER: ANTHROPIC_API_KEY nicht gesetzt!")
        sys.exit(1)
    
    # Verarbeite alle Protokolle
    results = []
    total_questions = 0
    total_duration = 0
    
    for protocol_path in protocol_files:
        result = await process_protocol(protocol_path, output_dir)
        results.append(result)
        
        if "error" not in result:
            total_questions += result.get("_question_count", 0)
            total_duration += result.get("_duration_seconds", 0)
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)
    
    successful = sum(1 for r in results if "error" not in r)
    failed = len(results) - successful
    
    print(f"\n  Verarbeitet: {len(results)} Protokolle")
    print(f"  Erfolgreich: {successful}")
    print(f"  Fehlgeschlagen: {failed}")
    print(f"  Gesamt Fragen: {total_questions}")
    print(f"  Gesamt Dauer: {total_duration:.1f}s")
    print(f"  Durchschnitt pro Protokoll: {total_duration/successful:.1f}s" if successful else "")
    
    print(f"\n  Output-Verzeichnis: {output_dir}")
    
    # Speichere Zusammenfassung
    summary_path = output_dir / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_protocols": len(results),
        "successful": successful,
        "failed": failed,
        "total_questions": total_questions,
        "total_duration_seconds": round(total_duration, 1),
        "results": [
            {
                "file": r.get("protocol_file"),
                "name": r.get("protocol_name"),
                "questions": r.get("_question_count", 0),
                "duration": r.get("_duration_seconds", 0),
                "error": r.get("error")
            }
            for r in results
        ]
    }
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"  Zusammenfassung: {summary_path.name}")
    
    print("\n" + "="*60)
    print("BATCH TEST ABGESCHLOSSEN")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
