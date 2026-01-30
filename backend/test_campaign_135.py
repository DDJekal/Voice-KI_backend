# -*- coding: utf-8 -*-
"""
Test: Question Generation fuer Campaign 135 via API

Nutzt die gleiche API-Anbindung wie auf Render:
1. Holt Protokoll von HOC API (/applicants/new)
2. Generiert Fragen lokal oder via Render
3. Speichert Ergebnis in test_output

Usage:
    cd backend
    python test_campaign_135.py                    # Campaign 135 via API
    python test_campaign_135.py 292                # Andere Campaign ID
    python test_campaign_135.py protocol_135.json  # Nutzt lokale Datei
    python test_campaign_135.py --render           # Sendet an Render statt lokal
"""

import json
import sys
import os
import requests
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.data_sources.api_loader import APIDataSource


CAMPAIGN_ID = 135
API_URL = "https://high-office.hirings.cloud/api/v1"
RENDER_BACKEND_URL = "https://voice-ki-backend.onrender.com/webhook/process-protocol"


def load_protocol_from_file(file_path: Path) -> dict:
    """Laedt Protokoll aus lokaler JSON-Datei."""
    print(f"\n[FILE] Lade Protokoll aus: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Unterstuetze verschiedene Formate
    if 'transcript' in data:
        protocol = data['transcript']
    elif 'pages' in data:
        protocol = data
    else:
        protocol = data
    
    print(f"   [OK] Name: {protocol.get('name', 'Unknown')}")
    print(f"   [OK] Pages: {len(protocol.get('pages', []))}")
    
    # Zaehle Prompts
    total_prompts = sum(len(p.get('prompts', [])) for p in protocol.get('pages', []))
    print(f"   [OK] Prompts: {total_prompts}")
    
    return protocol


def load_protocol_via_api(campaign_id: int, api_key: str) -> dict:
    """
    Laedt Protokoll ueber die HOC API (wie auf Render).
    
    Nutzt APIDataSource - exakt wie CampaignPackageBuilder.
    """
    print(f"\n[API] Lade Protokoll fuer Campaign {campaign_id}...")
    print(f"   URL: {API_URL}")
    print(f"   Key: {api_key[:20]}...")
    
    # Nutze die gleiche Klasse wie auf Render
    api_source = APIDataSource(
        api_url=API_URL,
        api_key=api_key,
        status="new",
        filter_test_applicants=True
    )
    
    try:
        # Hole Protokoll - wie CampaignPackageBuilder es macht
        protocol = api_source.get_conversation_protocol(str(campaign_id))
        
        print(f"   [OK] Protokoll: {protocol.get('name', 'Unknown')}")
        print(f"   [OK] ID: {protocol.get('id', 'N/A')}")
        print(f"   [OK] Pages: {len(protocol.get('pages', []))}")
        
        # Zaehle Prompts
        total_prompts = sum(len(p.get('prompts', [])) for p in protocol.get('pages', []))
        print(f"   [OK] Prompts: {total_prompts}")
        
        return protocol
        
    except ValueError as e:
        print(f"   [ERROR] {e}")
        
        # Zeige verfuegbare Campaigns
        try:
            print("\n[INFO] Versuche verfuegbare Campaigns zu listen...")
            applicants = api_source.list_pending_applicants()
            if applicants:
                campaign_ids = set(a.get('campaign_id') for a in applicants if a.get('campaign_id'))
                print(f"   [INFO] Campaigns mit Applicants: {sorted(campaign_ids)}")
            else:
                print("   [INFO] Keine Applicants gefunden")
        except Exception as list_err:
            print(f"   [WARN] Konnte Campaigns nicht listen: {list_err}")
        
        raise


def send_to_render_backend(protocol: dict, webhook_secret: str) -> dict:
    """
    Sendet Protokoll an das Render-Backend (wie HOC).
    """
    print(f"\n[RENDER] Sende Protokoll an Backend...")
    print(f"   URL: {RENDER_BACKEND_URL}")
    
    headers = {
        'Authorization': f'Bearer {webhook_secret}',
        'Content-Type': 'application/json'
    }
    
    import time
    start = time.time()
    
    response = requests.post(
        RENDER_BACKEND_URL,
        headers=headers,
        json=protocol,
        timeout=120
    )
    
    duration = time.time() - start
    
    print(f"   [OK] Status: {response.status_code}")
    print(f"   [OK] Dauer: {duration:.1f}s")
    
    if response.status_code != 200:
        print(f"   [ERROR] Response: {response.text[:500]}")
        raise Exception(f"Backend Error: {response.status_code}")
    
    result = response.json()
    print(f"   [OK] Fragen: {result.get('question_count', 0)}")
    
    kb = result.get('knowledge_base')
    if kb:
        print(f"   [OK] Knowledge-Base: {len(kb)} Kategorien")
    
    return result


def generate_locally(protocol: dict) -> dict:
    """
    Generiert Fragen lokal (ohne Render).
    """
    import asyncio
    from src.questions.builder import build_question_catalog
    
    print(f"\n[LOCAL] Generiere Fragen lokal...")
    
    settings = get_settings()
    # Aktiviere Unified Pipeline (wie auf Render mit USE_UNIFIED_PIPELINE=true)
    original_setting = settings.use_unified_pipeline
    settings.use_unified_pipeline = True
    
    print(f"   Pipeline: UNIFIED (wie auf Render)")
    print(f"   Claude First: {settings.use_claude_first}")
    
    import time
    start = time.time()
    
    try:
        async def run():
            context = {"policy_level": "standard"}
            return await build_question_catalog(protocol, context)
        
        catalog = asyncio.run(run())
        duration = time.time() - start
        
        # Extrahiere Knowledge-Base
        knowledge_base = getattr(catalog, 'knowledge_base', None)
        
        result = {
            "protocol_id": protocol.get('id', 0),
            "protocol_name": protocol.get('name', 'Unknown'),
            "processed_at": datetime.utcnow().isoformat() + "Z",
            "question_count": len(catalog.questions),
            "questions": [q.model_dump() for q in catalog.questions],
            "knowledge_base": knowledge_base or {},
            "_duration_seconds": round(duration, 1),
            "_generated_locally": True,
            "_pipeline": "UNIFIED"
        }
        
        print(f"   [OK] {len(catalog.questions)} Fragen generiert in {duration:.1f}s")
        
        if knowledge_base:
            print(f"   [OK] Knowledge-Base: {len(knowledge_base)} Kategorien")
        
        return result
        
    finally:
        settings.use_unified_pipeline = original_setting


def main():
    """
    Hauptfunktion: Laedt Protokoll via API und generiert Fragebogen.
    """
    print("=" * 70)
    print("   TEST: Question Generation via HOC API")
    print("=" * 70)
    
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    protocol = None
    campaign_id = CAMPAIGN_ID
    use_render = False
    use_file = None
    
    # Parse Argumente
    for arg in sys.argv[1:]:
        if arg == "--render":
            use_render = True
            print("[ARG] Render-Modus aktiviert")
        elif arg == "--local":
            use_render = False
            print("[ARG] Lokal-Modus aktiviert")
        elif arg.isdigit():
            campaign_id = int(arg)
            print(f"[ARG] Campaign ID: {campaign_id}")
        elif Path(arg).exists() or (Path(__file__).parent / arg).exists():
            use_file = arg
            print(f"[ARG] Datei: {arg}")
    
    # API Key aus .env laden
    settings = get_settings()
    api_key = getattr(settings, 'api_key', None) or ''
    webhook_secret = ''
    
    # Fallback: Direkt aus .env lesen
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                elif line.startswith('WEBHOOK_SECRET='):
                    webhook_secret = line.split('=', 1)[1].strip()
    
    # 1. Protokoll laden
    if use_file:
        # Aus Datei laden
        file_path = Path(use_file)
        if not file_path.exists():
            file_path = Path(__file__).parent / use_file
        if not file_path.exists():
            file_path = output_dir / use_file
        
        if file_path.exists():
            protocol = load_protocol_from_file(file_path)
            campaign_id = protocol.get('id', campaign_id)
    else:
        # Aus API laden
        if not api_key:
            print("[ERROR] Kein API_KEY in .env gefunden!")
            print("[INFO] Bitte setze API_KEY=... in backend/.env")
            sys.exit(1)
        
        try:
            protocol = load_protocol_via_api(campaign_id, api_key)
        except Exception as e:
            print(f"\n[ERROR] API-Zugriff fehlgeschlagen: {e}")
            
            # Fallback auf test_data
            test_data_dir = Path(__file__).parent / "test_data"
            test_files = sorted(test_data_dir.glob("*.json"))
            
            if test_files:
                print(f"\n[FALLBACK] Nutze lokale Datei: {test_files[0].name}")
                protocol = load_protocol_from_file(test_files[0])
                campaign_id = protocol.get('id', 'test')
            else:
                print("[ERROR] Keine Fallback-Daten verfuegbar")
                sys.exit(1)
    
    # 2. Protokoll speichern
    protocol_path = output_dir / f"protocol_{campaign_id}.json"
    with open(protocol_path, 'w', encoding='utf-8') as f:
        json.dump(protocol, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVE] Protokoll gespeichert: {protocol_path.name}")
    
    # 3. Fragen generieren
    try:
        if use_render:
            if not webhook_secret:
                print("[WARN] Kein WEBHOOK_SECRET - wechsle zu lokal")
                use_render = False
        
        if use_render:
            result = send_to_render_backend(protocol, webhook_secret)
        else:
            result = generate_locally(protocol)
        
        # 4. Ergebnis speichern
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_path = output_dir / f"questions_{campaign_id}_{timestamp}.json"
        
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n[SAVE] Fragebogen gespeichert: {result_path.name}")
        
        # 5. Fragen anzeigen
        questions = result.get('questions', [])
        if questions:
            print(f"\n[FRAGEN] Generierte Fragen ({len(questions)}):")
            for i, q in enumerate(questions[:12], 1):
                q_text = q.get('question', '')[:50]
                if len(q.get('question', '')) > 50:
                    q_text += "..."
                phase = q.get('phase', '?')
                qtype = q.get('type', '?')[:8]
                print(f"   {i:2}. [P{phase}] [{qtype:8}] {q_text}")
            
            if len(questions) > 12:
                print(f"       ... und {len(questions) - 12} weitere")
        
        # 6. Zusammenfassung
        print("\n" + "=" * 70)
        print("   ZUSAMMENFASSUNG")
        print("=" * 70)
        print(f"   Campaign:        {campaign_id}")
        print(f"   Protokoll:       {result.get('protocol_name', 'Unknown')}")
        print(f"   Modus:           {'Render' if not result.get('_generated_locally') else 'Lokal'}")
        print(f"   Pipeline:        {result.get('_pipeline', 'LEGACY')}")
        print(f"   Fragen:          {result.get('question_count', len(questions))}")
        kb = result.get('knowledge_base', {})
        print(f"   Knowledge-Base:  {len(kb)} Kategorien")
        if result.get('_duration_seconds'):
            print(f"   Dauer:           {result['_duration_seconds']}s")
        print(f"   Output:          {result_path}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[ERROR] FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
