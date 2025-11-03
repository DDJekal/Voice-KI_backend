"""
Generiere questions.json für Gesprächsprotokoll_Beispiel1.json (Projektleiter Elektrotechnik)
"""
import json
from pathlib import Path

# Lade Gesprächsprotokoll_Beispiel1
input_file = Path("../Input_ordner/Gesprächsprotokoll_Beispiel1.json")
with open(input_file, 'r', encoding='utf-8') as f:
    protokoll = json.load(f)

questions = []

# 1. IDENTIFIKATION
questions.append({
    "id": "adresse_bestaetigen",
    "question": "Ich habe Ihre Adresse als Mustermannstraße 3, 79098 Freiburg. Ist das korrekt?",
    "type": "boolean",
    "required": True,
    "priority": 1,
    "group": "Kontakt",
    "category": "identifikation",
    "category_order": 1,
    "source": {"verbatim": False}
})

# 2. STANDARDQUALIFIKATIONEN (GATE) - aus Page 1
gate_questions = []
page1 = protokoll["pages"][0]  # "Der Bewerber erfüllt folgende Kriterien"
for prompt in page1["prompts"]:
    q_text = prompt["question"]
    is_mandatory = "zwingend" in q_text.lower()
    
    gate_questions.append({
        "id": f"kriterium_{prompt['id']}",
        "question": q_text,
        "type": "boolean",
        "required": is_mandatory,
        "priority": 1 if is_mandatory else 2,
        "group": "Qualifikation",
        "category": "standardqualifikationen",
        "category_order": 3,
        "source": {
            "page_id": page1["id"],
            "prompt_id": prompt["id"],
            "verbatim": True
        },
        "context": "Muss-Kriterium" if is_mandatory else "Wünschenswert"
    })

# Sortiere: Zwingende zuerst
gate_questions.sort(key=lambda x: (not x["required"], x["priority"]))
questions.extend(gate_questions)

# 3. INFO - aus Page 3 "Weitere Informationen"
info_items = []
page3 = protokoll["pages"][2]  # "Weitere Informationen"
for prompt in page3["prompts"]:
    if prompt["type"] == "info":
        info_items.append({
            "id": f"info_{prompt['id']}",
            "question": prompt["question"],
            "type": "info",
            "required": False,
            "priority": 3,
            "group": "Info",
            "category": "info",
            "category_order": 4,
            "source": {
                "page_id": page3["id"],
                "prompt_id": prompt["id"],
                "verbatim": True
            }
        })

questions.extend(info_items)

# 4. STANDORT - aus Info extrahiert (Standort: Am Fichtenkamp 7-9 Bünde)
questions.append({
    "id": "standort_bestaetigung",
    "question": "Die Stelle ist am Standort Am Fichtenkamp 7-9 in Bünde. Ist das für Sie erreichbar?",
    "type": "boolean",
    "required": True,
    "priority": 1,
    "group": "Standort",
    "category": "standort",
    "category_order": 5,
    "source": {"verbatim": False}
})

# 5. EINSATZBEREICHE - aus Info extrahiert
questions.append({
    "id": "einsatzbereich_interesse",
    "question": "Wir arbeiten in verschiedenen Bereichen: Photovoltaik, Windkraft, E-Mobilität mit Ladestationen, und Netzbetreiber-Projekte. Welcher Bereich spricht Sie am meisten an?",
    "type": "choice",
    "options": [
        "Photovoltaik (große Solarparks)",
        "Windkraft",
        "E-Mobilität (Ladestationen)",
        "Netzbetreiber-Projekte",
        "Alle Bereiche interessieren mich"
    ],
    "required": False,
    "priority": 2,
    "group": "Einsatzbereich",
    "category": "einsatzbereiche",
    "category_order": 6,
    "source": {"verbatim": False}
})

# 6. RAHMENBEDINGUNGEN - aus Page 2
rahmen_items = []
page2 = protokoll["pages"][1]  # "Der Bewerber akzeptiert folgende Rahmenbedingungen"
for prompt in page2["prompts"]:
    rahmen_items.append({
        "id": f"rahmen_{prompt['id']}",
        "question": prompt["question"],
        "type": "boolean",
        "required": False,
        "priority": 2,
        "group": "Rahmen",
        "category": "rahmenbedingungen",
        "category_order": 7,
        "source": {
            "page_id": page2["id"],
            "prompt_id": prompt["id"],
            "verbatim": True
        }
    })

questions.extend(rahmen_items)

# 7. ZUSÄTZLICHE INFOS
questions.append({
    "id": "fuehrerschein_verfuegbar",
    "question": "Haben Sie einen Führerschein?",
    "type": "boolean",
    "required": False,
    "priority": 2,
    "group": "Zusätzlich",
    "category": "zusaetzliche_informationen",
    "category_order": 8,
    "source": {"verbatim": False},
    "context": "Wünschenswert für Außeneinsätze"
})

# Output
output = {
    "_meta": {
        "schema_version": "1.0",
        "generated_at": "2025-10-27T13:30:00.000Z",
        "generator": "python-enhanced-generator@1.0.0",
        "source": "Gesprächsprotokoll_Beispiel1.json",
        "note": "Projektleiter Elektrotechnik / Erneuerbare Energien"
    },
    "questions": questions
}

# Speichere
output_file = Path("questions_beispiel1.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✅ questions_beispiel1.json erstellt mit {len(questions)} Fragen")
print(f"\n📊 Kategorien:")
for cat_order in range(1, 9):
    cat_questions = [q for q in questions if q.get("category_order") == cat_order]
    if cat_questions:
        cat_name = cat_questions[0].get("category", "unbekannt")
        print(f"   {cat_order}. {cat_name.upper()}: {len(cat_questions)} Frage(n)")

# Zeige Gate-Questions an
gate_qs = [q for q in questions if q.get("category") == "standardqualifikationen" and q.get("required")]
print(f"\n⚠️  Gate-Questions (zwingend): {len(gate_qs)}")
for gq in gate_qs:
    print(f"   - {gq['question'][:60]}...")

