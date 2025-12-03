import json

print("="*70)
print("PRÜFUNG: Unternehmensprofil (Onboarding) Integration")
print("="*70)

# Campaign 258
with open('campaign_packages/258.json', encoding='utf-8') as f:
    c258 = json.load(f)

phase2 = c258['kb_templates']['phase_2']
phase1 = c258['kb_templates']['phase_1']

print("\n📦 Campaign 258 (Wege Klinik)\n")

# Phase 2 prüfen
print("="*70)
print("PHASE 2: UNTERNEHMENSVORSTELLUNG (erste 1500 Zeichen)")
print("="*70)
print(phase2[:1500])
print("\n...")

# Onboarding-Variablen prüfen
print("\n" + "="*70)
print("✅ ONBOARDING-VARIABLEN IN PHASE 2:")
print("="*70)

variables = {
    '{{companyname}}': 'Unternehmensname',
    '{{companysize}}': 'Unternehmensgröße',
    '{{companypitch}}': 'Benefits/Vorteile',
    '{{companypriorities}}': 'Schwerpunkte/Prioritäten',
    '{{campaignlocation_label}}': 'Standort',
    '{{campaignrole_title}}': 'Job-Titel'
}

found_vars = []
missing_vars = []

for var, description in variables.items():
    if var in phase2:
        found_vars.append(f"✅ {var} - {description}")
    else:
        missing_vars.append(f"❌ {var} - {description} FEHLT")

for var in found_vars:
    print(var)

if missing_vars:
    print("\n⚠️  FEHLENDE VARIABLEN:")
    for var in missing_vars:
        print(var)

# Company Name direkt prüfen
print("\n" + "="*70)
print("METADATA:")
print("="*70)
print(f"Company: {c258['company_name']}")
print(f"Campaign: {c258['campaign_name']}")
print(f"Questions: {len(c258['questions']['questions'])}")

print("\n" + "="*70)
print("FAZIT:")
print("="*70)
if len(missing_vars) == 0:
    print("✅ Unternehmensprofil vollständig integriert!")
    print("✅ Alle Onboarding-Daten vorhanden in Phase 2!")
else:
    print("⚠️  Einige Onboarding-Variablen fehlen!")
print("="*70)

