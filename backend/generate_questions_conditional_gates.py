"""
Verbesserte Version: questions.json mit konditionaler Gate-Logik
Alternativen werden abgefragt, bevor das Gespräch beendet wird
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

# 2. STANDARDQUALIFIKATIONEN (GATE) - MIT KONDITIONALER LOGIK

# Gate 1: Berufserfahrung (einfach, keine Alternativen)
questions.append({
    "id": "kriterium_berufserfahrung",
    "question": "Haben Sie mindestens 2 Jahre Berufserfahrung in Deutschland im Bereich Elektrotechnik?",
    "type": "boolean",
    "required": True,
    "priority": 1,
    "group": "Qualifikation",
    "category": "standardqualifikationen",
    "category_order": 3,
    "source": {
        "page_id": 90,
        "prompt_id": 315,
        "verbatim": True
    },
    "context": "Muss-Kriterium (Gate-Question)",
    "gate_config": {
        "is_gate": True,
        "can_end_call": True,
        "has_alternatives": False,
        "end_message": "Vielen Dank für Ihre Offenheit. Leider ist eine Berufserfahrung von mindestens 2 Jahren in Deutschland eine zwingende Voraussetzung für diese Stelle. Deshalb müssen wir das Gespräch an dieser Stelle beenden. Vielen Dank für Ihr Interesse und alles Gute für Ihre weitere Suche."
    }
})

# Gate 2: Studium Elektrotechnik (MIT Alternativen!)
questions.append({
    "id": "kriterium_studium",
    "question": "Haben Sie ein Studium in Elektrotechnik oder einem eng verwandten Bereich abgeschlossen?",
    "type": "boolean",
    "required": True,
    "priority": 1,
    "group": "Qualifikation",
    "category": "standardqualifikationen",
    "category_order": 3,
    "source": {
        "page_id": 90,
        "prompt_id": 313,
        "verbatim": True
    },
    "context": "Muss-Kriterium mit Alternativen (Gate-Question)",
    "gate_config": {
        "is_gate": True,
        "can_end_call": True,
        "has_alternatives": True,
        "alternative_question_ids": ["kriterium_elektriker", "kriterium_elektrofachkraft"],
        "logic": "IF studium = NEIN THEN check_alternatives ELSE continue"
    }
})

# Alternative 1: Ausbildung Elektriker (wird nur gefragt wenn Studium = NEIN)
questions.append({
    "id": "kriterium_elektriker",
    "question": "Haben Sie alternativ eine Ausbildung zum Elektriker, Elektrotechniker oder Elektroniker abgeschlossen?",
    "type": "boolean",
    "required": False,
    "priority": 1,
    "group": "Qualifikation",
    "category": "standardqualifikationen",
    "category_order": 3,
    "source": {
        "page_id": 90,
        "prompt_id": 317,
        "verbatim": True
    },
    "context": "Alternative zum Studium",
    "conditions": [{
        "when": {"field": "kriterium_studium", "op": "eq", "value": False},
        "then": {"action": "ask"}
    }],
    "gate_config": {
        "is_alternative": True,
        "alternative_for": "kriterium_studium",
        "can_satisfy_gate": True
    }
})

# Alternative 2: Elektrofachkraft (wird nur gefragt wenn beide vorherigen NEIN)
questions.append({
    "id": "kriterium_elektrofachkraft",
    "question": "Haben Sie eine Ausbildung zur Elektrofachkraft absolviert?",
    "type": "boolean",
    "required": False,
    "priority": 1,
    "group": "Qualifikation",
    "category": "standardqualifikationen",
    "category_order": 3,
    "source": {
        "page_id": 90,
        "prompt_id": 319,
        "verbatim": True
    },
    "context": "Alternative zum Studium",
    "conditions": [
        {"when": {"field": "kriterium_studium", "op": "eq", "value": False}, "then": {"action": "ask"}},
        {"when": {"field": "kriterium_elektriker", "op": "eq", "value": False}, "then": {"action": "ask"}}
    ],
    "gate_config": {
        "is_alternative": True,
        "alternative_for": "kriterium_studium",
        "can_satisfy_gate": True,
        "final_alternative": True,
        "end_message_if_all_no": "Vielen Dank für Ihre Offenheit. Leider benötigen wir für diese Stelle entweder ein Studium in Elektrotechnik oder eine abgeschlossene Ausbildung als Elektriker/Elektrofachkraft. Deshalb müssen wir das Gespräch an dieser Stelle beenden. Vielen Dank für Ihr Interesse und alles Gute für Ihre weitere Suche."
    }
})

# Wünschenswerte Kriterien (NACH Gate-Check)
questions.append({
    "id": "kriterium_deutsch_b2",
    "question": "Verfügen Sie über Deutschkenntnisse auf B2-Niveau?",
    "type": "boolean",
    "required": False,
    "priority": 2,
    "group": "Qualifikation",
    "category": "standardqualifikationen",
    "category_order": 3,
    "source": {
        "page_id": 90,
        "prompt_id": 311,
        "verbatim": True
    },
    "context": "Wünschenswert"
})

questions.append({
    "id": "kriterium_fuehrerschein",
    "question": "Besitzen Sie einen Führerschein?",
    "type": "boolean",
    "required": False,
    "priority": 3,
    "group": "Qualifikation",
    "category": "standardqualifikationen",
    "category_order": 3,
    "source": {
        "page_id": 90,
        "prompt_id": 321,
        "verbatim": True
    },
    "context": "Wünschenswert für Außeneinsätze"
})

# 3. INFO - aus Page 3 "Weitere Informationen"
info_items = []
page3 = protokoll["pages"][2]
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

# 4. STANDORT
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

# 5. EINSATZBEREICHE
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

# 6. RAHMENBEDINGUNGEN
rahmen_items = []
page2 = protokoll["pages"][1]
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

# Output
output = {
    "_meta": {
        "schema_version": "1.1",
        "generated_at": "2025-10-27T13:35:00.000Z",
        "generator": "python-conditional-gate-generator@1.1.0",
        "source": "Gesprächsprotokoll_Beispiel1.json",
        "note": "Projektleiter Elektrotechnik mit konditionaler Gate-Logik",
        "features": ["conditional_gates", "alternative_checks"]
    },
    "questions": questions
}

# Speichere
output_file = Path("questions_beispiel1_conditional.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✅ questions_beispiel1_conditional.json erstellt mit {len(questions)} Fragen")
print(f"\n📊 Gate-Struktur:")
print(f"   Gate 1: Berufserfahrung (keine Alternativen)")
print(f"   Gate 2: Studium Elektrotechnik")
print(f"     → Alternative 1: Ausbildung Elektriker")
print(f"     → Alternative 2: Ausbildung Elektrofachkraft")
print(f"\n💡 Logik:")
print(f"   IF Studium = JA → weiter")
print(f"   IF Studium = NEIN → Alternative 1 fragen")
print(f"     IF Alternative 1 = JA → weiter")
print(f"     IF Alternative 1 = NEIN → Alternative 2 fragen")
print(f"       IF Alternative 2 = JA → weiter")
print(f"       IF Alternative 2 = NEIN → Gespräch beenden")

