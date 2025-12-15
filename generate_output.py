import json
import asyncio
from backend.src.questions.builder import build_question_catalog

async def main():
    print('='*80)
    print('GENERIERE JSON-AUSGABE FÜR HOC')
    print('='*80)
    
    # Lade Protocol
    with open('Input_ordner/Gesprächsprotokoll_Teil3.json', 'r', encoding='utf-8') as f:
        protocol = json.load(f)
    
    print(f'\n📋 Input: {protocol["name"]} (ID: {protocol["id"]})')
    
    # Generiere Questions
    context = {'policy_level': 'standard'}
    catalog = await build_question_catalog(protocol, context)
    
    print(f'✅ {len(catalog.questions)} Fragen generiert')
    
    # Trim questions - nur Export-Felder (wie HOC sie empfängt)
    EXPORT_FIELDS = {
        'id', 'question', 'preamble', 'group', 'context',
        'category', 'category_order', 'type', 'options',
        'priority', 'help_text'
    }
    
    trimmed_questions = []
    for q in catalog.questions:
        q_dict = q.model_dump()
        trimmed = {
            key: value 
            for key, value in q_dict.items() 
            if key in EXPORT_FIELDS and value is not None
        }
        trimmed_questions.append(trimmed)
    
    # Erstelle Output-Struktur (wie sie HOC empfängt)
    output = {
        'protocol_id': protocol['id'],
        'protocol_name': protocol['name'],
        'question_count': len(trimmed_questions),
        'questions': trimmed_questions
    }
    
    # Speichere
    output_file = 'Output_ordner/Pflegefachkraefte_Output.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f'\n💾 Gespeichert: {output_file}')
    print(f'\n📊 Statistik:')
    
    # Gruppiere nach Type
    by_type = {}
    for q in trimmed_questions:
        qtype = q.get('type', 'unknown')
        by_type[qtype] = by_type.get(qtype, 0) + 1
    
    print('\n   Nach Type:')
    for qtype, count in sorted(by_type.items()):
        print(f'     - {qtype}: {count}')
    
    # Gruppiere nach Group
    by_group = {}
    for q in trimmed_questions:
        group = q.get('group', 'unknown')
        by_group[group] = by_group.get(group, 0) + 1
    
    print('\n   Nach Group:')
    for group, count in sorted(by_group.items(), key=lambda x: -x[1]):
        print(f'     - {group}: {count}')
    
    # Zeige Stationen/Fachabteilungen (wichtig für Healthcare-Erkennung)
    print('\n🏥 Standorte & Stationen:')
    print('='*80)
    
    # Standort-Fragen
    site_questions = [q for q in trimmed_questions if 'standort' in q['id'].lower() or q.get('group') == 'Standort']
    for q in site_questions:
        print(f'\nID: {q["id"]}')
        if 'preamble' in q and q['preamble']:
            print(f'Preamble: {q["preamble"][:100]}...' if len(q.get("preamble", "")) > 100 else f'Preamble: {q.get("preamble")}')
        print(f'Frage: {q["question"]}')
        if 'options' in q and q['options']:
            print(f'Optionen ({len(q["options"])}): {", ".join(q["options"][:3])}...')
    
    # Department/Stations-Fragen
    dept_questions = [q for q in trimmed_questions if 'department' in q['id'].lower() or 'station' in q['id'].lower() or q.get('group') == 'Einsatzbereich']
    for q in dept_questions:
        print(f'\nID: {q["id"]}')
        if 'preamble' in q and q['preamble']:
            print(f'Preamble: {q["preamble"][:150]}...' if len(q.get("preamble", "")) > 150 else f'Preamble: {q.get("preamble")}')
        print(f'Frage: {q["question"]}')
        if 'options' in q and q['options']:
            print(f'Optionen ({len(q["options"])}): {", ".join(q["options"][:5])}...')
    
    # Zeige konsolidierte Qualifikations-Frage
    print('\n🎯 Qualifikations-Fragen:')
    print('='*80)
    
    qual_questions = [q for q in trimmed_questions if q.get('group') == 'Qualifikation']
    for q in qual_questions[:3]:  # Zeige erste 3
        print(f'\nID: {q["id"]}')
        if 'preamble' in q and q['preamble']:
            print(f'Preamble: {q["preamble"]}')
        print(f'Frage: {q["question"]}')
        print(f'Type: {q["type"]}')
        if 'options' in q and q['options']:
            print(f'Optionen ({len(q["options"])}):')
            for i, opt in enumerate(q['options'], 1):
                print(f'  {i}. {opt}')
    
    print(f'\n✅ Fertig! Vollständige JSON-Ausgabe siehe: {output_file}')

if __name__ == '__main__':
    asyncio.run(main())

