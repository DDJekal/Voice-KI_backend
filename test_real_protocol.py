import json
import asyncio
from backend.src.questions.builder import build_question_catalog
from backend.src.questions.pipeline.extract import extract

async def test():
    print('='*80)
    print('TEST: Gesprächsprotokoll Beispiel1 - Projektleiter Elektrotechnik')
    print('='*80)
    
    # Lade Protocol
    with open('Input_ordner/Gesprächsprotokoll_Beispiel1.json', 'r', encoding='utf-8') as f:
        protocol = json.load(f)
    
    protocol_id = protocol.get('id')
    protocol_name = protocol.get('name')
    pages = protocol.get('pages', [])
    
    print(f'\n📋 PROTOCOL INFO:')
    print(f'   ID: {protocol_id}')
    print(f'   Name: {protocol_name}')
    print(f'   Pages: {len(pages)}')
    
    # Zeige Kriterien
    if pages:
        page_name = pages[0].get('name', '')
        print(f'\n📝 KRITERIEN (Page 1 - {page_name}):')
        for prompt in pages[0].get('prompts', []):
            question = prompt.get('question', '')
            print(f'   - {question}')
    
    # Extract Phase
    print(f'\n🔍 EXTRACT PHASE:')
    print('='*80)
    
    extract_result = await extract(protocol)
    
    print(f'\nMust-Have ({len(extract_result.must_have)}):')
    for mh in extract_result.must_have:
        print(f'  ✓ {mh}')
    
    print(f'\nAlternatives ({len(extract_result.alternatives)}):')
    for alt in extract_result.alternatives:
        print(f'  ↔ {alt}')
    
    print(f'\nProtocol Questions ({len(extract_result.protocol_questions)}):')
    for pq in extract_result.protocol_questions[:5]:
        text_preview = pq.text[:70]
        print(f'  ? {text_preview}')
    if len(extract_result.protocol_questions) > 5:
        remaining = len(extract_result.protocol_questions) - 5
        print(f'  ... und {remaining} weitere')
    
    # Question Generation
    print(f'\n🎯 QUESTION GENERATION:')
    print('='*80)
    
    context = {'policy_level': 'standard'}
    catalog = await build_question_catalog(protocol, context)
    
    print(f'\n✅ Gesamt generierte Fragen: {len(catalog.questions)}')
    
    # Gruppiere nach Kategorie
    by_group = {}
    for q in catalog.questions:
        group = q.group or 'Andere'
        if group not in by_group:
            by_group[group] = []
        by_group[group].append(q)
    
    print(f'\n📊 Fragen nach Gruppe:')
    for group, questions in sorted(by_group.items()):
        print(f'   {group}: {len(questions)} Fragen')
    
    # Zeige Qualifikations-Fragen im Detail
    print(f'\n🎓 QUALIFIKATIONS-FRAGEN IM DETAIL:')
    print('='*80)
    
    qual_questions = by_group.get('Qualifikation', [])
    for i, q in enumerate(qual_questions, 1):
        print(f'\n{i}. ID: {q.id}')
        if q.preamble:
            preamble_preview = q.preamble[:60]
            print(f'   Preamble: {preamble_preview}...')
        print(f'   Frage: {q.question}')
        print(f'   Type: {q.type}')
        if q.options:
            opt_count = len(q.options)
            print(f'   Optionen ({opt_count}):')
            for opt in q.options[:3]:
                print(f'     - {opt}')
            if opt_count > 3:
                remaining_opts = opt_count - 3
                print(f'     ... und {remaining_opts} weitere')
        print(f'   Required: {q.required} | Priority: {q.priority}')
    
    # Zeige ALLE Fragen als Übersicht
    print(f'\n📋 ALLE GENERIERTEN FRAGEN (ÜBERSICHT):')
    print('='*80)
    for i, q in enumerate(catalog.questions, 1):
        group_name = q.group or 'Andere'
        print(f'{i:2d}. [{group_name:15s}] {q.question[:60]}')

asyncio.run(test())

