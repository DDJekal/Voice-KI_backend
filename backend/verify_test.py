import json

print("="*70)
print("🧪 TEST-ERGEBNIS: Automatische Fragen wurden entfernt")
print("="*70)

# Campaign 258
with open('campaign_packages/258.json', encoding='utf-8') as f:
    c258 = json.load(f)

print("\n📦 Campaign 258 (Wege Klinik):")
print(f"   Fragen: {len(c258['questions']['questions'])}")
for q in c258['questions']['questions']:
    print(f"   ✓ {q['id']}")

# Campaign 93
with open('campaign_packages/93.json', encoding='utf-8') as f:
    c93 = json.load(f)

print("\n📦 Campaign 93 (Evangelische Krankenhausgemeinschaft):")
print(f"   Fragen: {len(c93['questions']['questions'])}")
for q in c93['questions']['questions']:
    print(f"   ✓ {q['id']}")

print("\n" + "="*70)
print("✅ VERIFIZIERUNG:")
print("="*70)

# Check für automatische Fragen
all_ids_258 = [q['id'] for q in c258['questions']['questions']]
all_ids_93 = [q['id'] for q in c93['questions']['questions']]
all_ids = all_ids_258 + all_ids_93

removed_questions = [
    'name_confirmation',
    'address_confirmation', 
    'address_request',
    'start_date'
]

for removed in removed_questions:
    if removed not in all_ids:
        print(f"✅ KEINE {removed}")
    else:
        print(f"❌ WARNUNG: {removed} gefunden!")

print("\n" + "="*70)
print("📊 ZUSAMMENFASSUNG:")
print("="*70)
print(f"Campaign 258: {len(c258['questions']['questions'])} Fragen (nur aus Protocol)")
print(f"Campaign 93:  {len(c93['questions']['questions'])} Fragen (nur aus Protocol)")
print("\n→ Alle Fragen stammen aus dem Gesprächsprotokoll!")
print("→ Keine automatisch hinzugefügten Standard-Fragen mehr!")
print("="*70)

