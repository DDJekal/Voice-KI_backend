import json

with open('campaign_packages/258.json', encoding='utf-8') as f:
    data = json.load(f)

questions = data['questions']['questions']

print("="*70)
print("✅ ÄNDERUNG ERFOLGREICH: Nur Protocol-basierte Fragen!")
print("="*70)
print(f"\nAnzahl Fragen: {len(questions)}\n")
print("="*70)
print("GENERIERTE FRAGEN:")
print("="*70)

for i, q in enumerate(questions, 1):
    print(f"\n{i}. ID: {q['id']}")
    print(f"   Frage: {q['question']}")
    print(f"   Typ: {q['type']}")
    print(f"   Required: {q['required']}")

print("\n" + "="*70)
print("ENTFERNTE FRAGEN (nicht mehr automatisch):")
print("="*70)
print("❌ name_confirmation")
print("❌ address_confirmation")
print("❌ address_request")
print("❌ start_date")
print("\n→ Diese werden nur generiert wenn im Gesprächsprotokoll definiert!")
print("="*70)

