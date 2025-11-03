"""
Output Generator für Input_ordner mit Gesprächsprotokoll_Beispiel2
Verarbeitet die Daten und speichert strukturierte Outputs
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from src.data_sources.file_loader import FileDataSource
from src.aggregator.unified_aggregator import UnifiedAggregator
from src.aggregator.knowledge_base_builder import KnowledgeBaseBuilder


def generate_outputs():
    """Generiert alle Outputs und speichert sie im Output_ordner"""
    
    print("\n" + "="*70)
    print("📊 VoiceKI Output Generator")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    # Output-Verzeichnis
    output_dir = Path("Output_ordner")
    output_dir.mkdir(exist_ok=True)
    
    # Data Source mit Gesprächsprotokoll_Beispiel2
    print("📂 Schritt 1: Lade Daten aus Input_ordner...")
    data_dir = Path("../Input_ordner")
    
    # Temporär Gesprächsprotokoll_Beispiel2.json kopieren
    protocol_source = data_dir / "Gesprächsprotokoll_Beispiel2.json"
    protocol_target = data_dir / "Gesprächsprotokoll.json"
    
    # Kopiere Beispiel2 temporär
    if protocol_source.exists():
        import shutil
        shutil.copy(protocol_source, protocol_target)
        print(f"   ✓ Verwende Gesprächsprotokoll_Beispiel2.json")
    
    data_source = FileDataSource(str(data_dir))
    
    # Lade Daten
    applicant = data_source.get_applicant_profile("test")
    address = data_source.get_applicant_address("test")
    company = data_source.get_company_profile("test")
    protocol = data_source.get_conversation_protocol("test")
    
    print(f"   ✓ Bewerber: {applicant['first_name']} {applicant['last_name']}")
    print(f"   ✓ Unternehmen: {company['name']}")
    print(f"   ✓ Gesprächsprotokoll: {protocol['name']}")
    
    # Aggregiere Daten
    print("\n🔄 Schritt 2: Aggregiere Daten für alle Phasen...")
    aggregator = UnifiedAggregator()
    
    phase1_data = aggregator.aggregate_phase_1(applicant, address)
    print(f"   ✓ Phase 1: {len(phase1_data)} Variablen")
    
    phase2_data = aggregator.aggregate_phase_2(company)
    print(f"   ✓ Phase 2: {len(phase2_data)} Variablen")
    
    # Für Phase 3: Lade questions.json falls vorhanden
    questions_path = Path("../KI-Sellcruiting_VerarbeitungProtokollzuFragen/output/questions.json")
    if questions_path.exists():
        with open(questions_path, 'r', encoding='utf-8') as f:
            questions_json = json.load(f)
    else:
        questions_json = {"_meta": {}, "questions": []}
    
    phase3_data = aggregator.aggregate_phase_3(questions_json)
    print(f"   ✓ Phase 3: {phase3_data['total_questions']} Fragen")
    
    phase4_data = aggregator.aggregate_phase_4(applicant)
    print(f"   ✓ Phase 4: {len(phase4_data)} Variablen")
    
    # Erstelle Knowledge Bases
    print("\n📝 Schritt 3: Erstelle Knowledge Bases...")
    kb_builder = KnowledgeBaseBuilder()
    
    kb1 = kb_builder.build_phase_1(phase1_data)
    print(f"   ✓ Phase 1 KB: {len(kb1)} Zeichen")
    
    kb2 = kb_builder.build_phase_2(phase2_data)
    print(f"   ✓ Phase 2 KB: {len(kb2)} Zeichen")
    
    kb3 = kb_builder.build_phase_3(questions_json)
    print(f"   ✓ Phase 3 KB: {len(kb3)} Zeichen")
    
    kb4 = kb_builder.build_phase_4(phase4_data)
    print(f"   ✓ Phase 4 KB: {len(kb4)} Zeichen")
    
    # Kombinierte Knowledge Base
    combined_kb = "\n\n".join([
        "=" * 80,
        "MASTER KNOWLEDGE BASE - ALLE PHASEN",
        "=" * 80,
        kb1,
        kb2,
        kb3,
        kb4
    ])
    
    print(f"\n📦 Schritt 4: Speichere Outputs...")
    
    # 1. Speichere aggregierte Daten
    aggregated_output = {
        "_meta": {
            "generated_at": datetime.now().isoformat(),
            "generator": "voiceki-backend-output-generator",
            "input_source": "Input_ordner/",
            "protocol_used": "Gesprächsprotokoll_Beispiel2.json"
        },
        "phase_1": phase1_data,
        "phase_2": phase2_data,
        "phase_3": {
            "total_questions": phase3_data["total_questions"],
            "groups": phase3_data["groups"],
            "priority_questions_count": len(phase3_data["priority_questions"])
        },
        "phase_4": phase4_data
    }
    
    with open(output_dir / "aggregated_data.json", 'w', encoding='utf-8') as f:
        json.dump(aggregated_output, f, ensure_ascii=False, indent=2)
    print(f"   ✓ aggregated_data.json gespeichert")
    
    # 2. Speichere Knowledge Bases einzeln
    with open(output_dir / "knowledge_base_phase1.txt", 'w', encoding='utf-8') as f:
        f.write(kb1)
    print(f"   ✓ knowledge_base_phase1.txt gespeichert")
    
    with open(output_dir / "knowledge_base_phase2.txt", 'w', encoding='utf-8') as f:
        f.write(kb2)
    print(f"   ✓ knowledge_base_phase2.txt gespeichert")
    
    with open(output_dir / "knowledge_base_phase3.txt", 'w', encoding='utf-8') as f:
        f.write(kb3)
    print(f"   ✓ knowledge_base_phase3.txt gespeichert")
    
    with open(output_dir / "knowledge_base_phase4.txt", 'w', encoding='utf-8') as f:
        f.write(kb4)
    print(f"   ✓ knowledge_base_phase4.txt gespeichert")
    
    # 3. Speichere kombinierte Knowledge Base
    with open(output_dir / "knowledge_base_combined.txt", 'w', encoding='utf-8') as f:
        f.write(combined_kb)
    print(f"   ✓ knowledge_base_combined.txt gespeichert ({len(combined_kb)} Zeichen)")
    
    # 4. Speichere Rohdaten für Referenz
    raw_data = {
        "_meta": {
            "generated_at": datetime.now().isoformat(),
            "source": "Input_ordner/"
        },
        "applicant_profile": applicant,
        "applicant_address": address,
        "company_profile": company,
        "conversation_protocol": protocol
    }
    
    with open(output_dir / "raw_input_data.json", 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    print(f"   ✓ raw_input_data.json gespeichert")
    
    # 5. Erstelle Summary
    summary = f"""VoiceKI Backend - Output Summary
{"="*70}

Generiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Input Quelle: Input_ordner/
Gesprächsprotokoll: Gesprächsprotokoll_Beispiel2.json

BEWERBER
--------
Name: {applicant['first_name']} {applicant['last_name']}
Email: {applicant['email']}
Telefon: {applicant['telephone']}
Adresse: {address['street']} {address['house_number']}, {address['postal_code']} {address['city']}

UNTERNEHMEN
-----------
Name: {phase2_data['companyname']}
Größe: {phase2_data['companysize']} Mitarbeitende
Standort: {phase2_data['campaignlocation_label']}

GESPRÄCHSPROTOKOLL
------------------
Titel: {protocol['name']}
Seiten: {len(protocol.get('pages', []))}
Kriterien: {len([p for page in protocol.get('pages', []) for p in page.get('prompts', []) if 'Kriterien' in page.get('name', '')])}
Rahmenbedingungen: {len([p for page in protocol.get('pages', []) for p in page.get('prompts', []) if 'Rahmenbedingungen' in page.get('name', '')])}

AGGREGIERTE DATEN
-----------------
Phase 1 Variablen: {len(phase1_data)}
Phase 2 Variablen: {len(phase2_data)}
Phase 3 Fragen: {phase3_data['total_questions']}
Phase 4 Variablen: {len(phase4_data)}

KNOWLEDGE BASES
---------------
Phase 1: {len(kb1)} Zeichen
Phase 2: {len(kb2)} Zeichen
Phase 3: {len(kb3)} Zeichen
Phase 4: {len(kb4)} Zeichen
Kombiniert: {len(combined_kb)} Zeichen

GENERIERTE DATEIEN
------------------
✓ aggregated_data.json          - Strukturierte aggregierte Daten
✓ knowledge_base_phase1.txt     - KB für Phase 1 (Begrüßung)
✓ knowledge_base_phase2.txt     - KB für Phase 2 (Unternehmensvorstellung)
✓ knowledge_base_phase3.txt     - KB für Phase 3 (Fragenkatalog)
✓ knowledge_base_phase4.txt     - KB für Phase 4 (Lebenslauf)
✓ knowledge_base_combined.txt   - Alle Phasen kombiniert
✓ raw_input_data.json           - Original Input-Daten
✓ output_summary.txt            - Diese Zusammenfassung

{"="*70}
"""
    
    with open(output_dir / "output_summary.txt", 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"   ✓ output_summary.txt gespeichert")
    
    # Aufräumen: Temporäre Kopie entfernen
    if protocol_target.exists():
        protocol_target.unlink()
    
    # Finale Ausgabe
    print("\n" + "="*70)
    print("✅ OUTPUT ERFOLGREICH GENERIERT!")
    print("="*70)
    print(f"\nOutput-Verzeichnis: {output_dir.absolute()}")
    print(f"\nGenerierte Dateien ({len(list(output_dir.glob('*')))} Dateien):")
    for file in sorted(output_dir.glob('*')):
        size = file.stat().st_size
        print(f"   📄 {file.name} ({size:,} Bytes)")
    
    print("\n" + summary)
    
    return output_dir


def main():
    """Hauptfunktion"""
    try:
        output_dir = generate_outputs()
        return 0
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

