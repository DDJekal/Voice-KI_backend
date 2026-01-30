"""
A/B Test: Claude vs. OpenAI für Fragengenerierung

Vergleicht die Qualität und Performance beider LLM-Provider
bei der Generierung von Recruiting-Fragebögen.

Usage:
    cd backend
    venv\\Scripts\\python test_claude_comparison.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.questions.builder import build_question_catalog
from src.questions.llm_adapter import call_llm_async


# Test-Protokolle
TEST_PROTOCOLS = {
    "kita": "test_protocol.json",
    "pflege": "mock_protocol.json",
}


def load_protocol(name: str = "kita") -> dict:
    """Lädt ein Test-Protokoll."""
    filename = TEST_PROTOCOLS.get(name, name)
    path = Path(__file__).parent / filename
    
    if not path.exists():
        print(f"Protokoll nicht gefunden: {path}")
        sys.exit(1)
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


async def test_simple_llm_call(provider: str):
    """
    Einfacher Test: Prüft ob der Provider funktioniert.
    """
    print(f"\n{'='*60}")
    print(f"SIMPLE TEST: {provider.upper()}")
    print('='*60)
    
    messages = [
        {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
        {"role": "user", "content": "Antworte mit genau einem Wort: Test"}
    ]
    
    try:
        start = time.time()
        result = await call_llm_async(
            messages=messages,
            temperature=0.0,
            force_provider=provider
        )
        duration = time.time() - start
        
        content = result["choices"][0]["message"]["content"]
        tokens = result.get("usage", {}).get("total_tokens", 0)
        
        print(f"Response: {content}")
        print(f"Duration: {duration:.2f}s")
        print(f"Tokens: {tokens}")
        print(f"Provider: {result.get('_provider', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"FEHLER: {e}")
        return False


async def generate_with_provider(protocol: dict, provider: str) -> dict:
    """
    Generiert Fragebogen mit spezifischem Provider.
    
    Setzt temporär die Config um den Provider zu forcen.
    """
    print(f"\n{'='*60}")
    print(f"GENERIERUNG MIT: {provider.upper()}")
    print('='*60)
    
    # Patch the llm_adapter to force provider
    import src.questions.llm_adapter as adapter
    original_call = adapter.call_llm_async
    
    async def patched_call(messages, temperature=0.7, response_format=None, timeout=None, force_provider=None):
        return await original_call(
            messages=messages,
            temperature=temperature,
            response_format=response_format,
            timeout=timeout,
            force_provider=provider  # Force the specific provider
        )
    
    # Patch in pipeline modules
    import src.questions.pipeline.classify as classify_module
    import src.questions.pipeline.extract_multistage as extract_module
    
    orig_classify = classify_module.call_llm_async
    orig_extract = extract_module.call_llm_async
    
    classify_module.call_llm_async = patched_call
    extract_module.call_llm_async = patched_call
    
    try:
        start = time.time()
        
        context = {"policy_level": "standard"}
        catalog = await build_question_catalog(protocol, context)
        
        duration = time.time() - start
        
        # Convert to dict
        result = {
            "questions": [q.model_dump() for q in catalog.questions],
            "meta": catalog.meta.model_dump() if catalog.meta else {},
            "_provider": provider,
            "_duration": duration,
            "_question_count": len(catalog.questions),
            "_generated_at": datetime.now().isoformat()
        }
        
        print(f"Generiert: {len(catalog.questions)} Fragen")
        print(f"Dauer: {duration:.1f}s")
        
        return result
        
    except Exception as e:
        print(f"FEHLER bei {provider}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "questions": [],
            "_provider": provider,
            "_duration": 0,
            "_error": str(e)
        }
    
    finally:
        # Restore originals
        classify_module.call_llm_async = orig_classify
        extract_module.call_llm_async = orig_extract


def compare_results(openai_result: dict, claude_result: dict):
    """
    Vergleicht die Ergebnisse beider Provider.
    """
    print(f"\n{'='*60}")
    print("VERGLEICH")
    print('='*60)
    
    # Basic metrics
    print(f"\n{'Metrik':<30} {'OpenAI':<15} {'Claude':<15}")
    print("-" * 60)
    
    # Question count
    o_count = len(openai_result.get("questions", []))
    c_count = len(claude_result.get("questions", []))
    print(f"{'Anzahl Fragen':<30} {o_count:<15} {c_count:<15}")
    
    # Duration
    o_dur = openai_result.get("_duration", 0)
    c_dur = claude_result.get("_duration", 0)
    print(f"{'Dauer (Sekunden)':<30} {o_dur:.1f}{'':>9} {c_dur:.1f}")
    
    # Preambles
    o_preambles = sum(1 for q in openai_result.get("questions", []) if q.get("preamble"))
    c_preambles = sum(1 for q in claude_result.get("questions", []) if q.get("preamble"))
    print(f"{'Preambles ausgefuellt':<30} {o_preambles:<15} {c_preambles:<15}")
    
    # Help texts
    o_help = sum(1 for q in openai_result.get("questions", []) if q.get("help_text"))
    c_help = sum(1 for q in claude_result.get("questions", []) if q.get("help_text"))
    print(f"{'Help-Texts ausgefuellt':<30} {o_help:<15} {c_help:<15}")
    
    # Errors
    o_err = "Ja" if openai_result.get("_error") else "Nein"
    c_err = "Ja" if claude_result.get("_error") else "Nein"
    print(f"{'Fehler aufgetreten':<30} {o_err:<15} {c_err:<15}")
    
    # Question details
    print(f"\n{'='*60}")
    print("FRAGEN-VERGLEICH")
    print('='*60)
    
    print("\n--- OpenAI Fragen ---")
    for i, q in enumerate(openai_result.get("questions", [])[:5], 1):
        question_text = q.get("question", "")[:60]
        q_type = q.get("type", "?")
        print(f"  {i}. [{q_type}] {question_text}...")
    
    if o_count > 5:
        print(f"  ... und {o_count - 5} weitere")
    
    print("\n--- Claude Fragen ---")
    for i, q in enumerate(claude_result.get("questions", [])[:5], 1):
        question_text = q.get("question", "")[:60]
        q_type = q.get("type", "?")
        print(f"  {i}. [{q_type}] {question_text}...")
    
    if c_count > 5:
        print(f"  ... und {c_count - 5} weitere")


def save_results(openai_result: dict, claude_result: dict):
    """
    Speichert beide Ergebnisse zur manuellen Analyse.
    """
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save OpenAI result
    openai_path = output_dir / f"comparison_openai_{timestamp}.json"
    with open(openai_path, 'w', encoding='utf-8') as f:
        json.dump(openai_result, f, ensure_ascii=False, indent=2)
    print(f"\nOpenAI Output: {openai_path}")
    
    # Save Claude result
    claude_path = output_dir / f"comparison_claude_{timestamp}.json"
    with open(claude_path, 'w', encoding='utf-8') as f:
        json.dump(claude_result, f, ensure_ascii=False, indent=2)
    print(f"Claude Output: {claude_path}")


async def main():
    """
    Hauptfunktion für A/B-Test.
    """
    print("="*60)
    print("    CLAUDE vs. OPENAI - A/B TEST")
    print("    Fragebogengenerierung")
    print("="*60)
    
    settings = get_settings()
    
    # Check API keys
    print("\n--- API Key Status ---")
    print(f"ANTHROPIC_API_KEY: {'Vorhanden' if settings.anthropic_api_key else 'FEHLT!'}")
    print(f"OPENAI_API_KEY: {'Vorhanden' if settings.openai_api_key else 'FEHLT!'}")
    print(f"Claude Model: {settings.anthropic_model}")
    print(f"OpenAI Model: {settings.openai_model}")
    
    if not settings.anthropic_api_key:
        print("\nFEHLER: ANTHROPIC_API_KEY nicht in .env gesetzt!")
        sys.exit(1)
    
    if not settings.openai_api_key:
        print("\nWARNUNG: OPENAI_API_KEY nicht gesetzt - nur Claude-Test moeglich")
    
    # Simple connectivity test
    print("\n--- Verbindungstests ---")
    
    claude_ok = await test_simple_llm_call("claude")
    
    if settings.openai_api_key:
        openai_ok = await test_simple_llm_call("openai")
    else:
        openai_ok = False
        print("OpenAI-Test uebersprungen (kein API Key)")
    
    if not claude_ok:
        print("\nClaude-Verbindung fehlgeschlagen!")
        sys.exit(1)
    
    # Load test protocol
    print("\n--- Lade Test-Protokoll ---")
    protocol = load_protocol("kita")
    print(f"Protokoll: {protocol.get('name', 'Unknown')}")
    print(f"Seiten: {len(protocol.get('pages', []))}")
    
    # Generate with both providers
    claude_result = await generate_with_provider(protocol, "claude")
    
    if openai_ok:
        openai_result = await generate_with_provider(protocol, "openai")
    else:
        openai_result = {"questions": [], "_error": "Kein API Key"}
    
    # Compare
    compare_results(openai_result, claude_result)
    
    # Save results
    save_results(openai_result, claude_result)
    
    print("\n" + "="*60)
    print("TEST ABGESCHLOSSEN")
    print("="*60)
    print("\nBitte pruefen Sie die gespeicherten JSON-Dateien manuell auf:")
    print("  - Grammatische Korrektheit der Fragen")
    print("  - Vollstaendigkeit der extrahierten Informationen")
    print("  - Qualitaet der Preambles und Help-Texts")


if __name__ == "__main__":
    asyncio.run(main())
