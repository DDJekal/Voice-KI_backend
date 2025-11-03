"""
Temporäres Skript um questions.json für Gesprächsprotokoll_Beispiel1.json zu generieren
Da das TypeScript Tool Cache-Probleme hat, extrahieren wir die Fragen direkt.
"""
import json
from pathlib import Path

# Lade Gesprächsprotokoll_Beispiel1
input_file = Path("../Input_ordner/Gesprächsprotokoll_Beispiel1.json")
with open(input_file, 'r', encoding='utf-8') as f:
    protokoll = json.load(f)

# Extrahiere Fragen
questions = []
question_id_counter = 1

# Identifikation: Adresse bestätigen
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

# Standardqualifikationen (Gate): Examinierte Pflegefachkraft
questions.append({
    "id": "examen_pflege",
    "question": "Sind Sie examinierte Pflegefachfrau oder Pflegefachmann?",
    "type": "boolean",
    "required": True,
    "priority": 1,
    "group": "Qualifikation",
    "category": "standardqualifikationen",
    "category_order": 3,
    "source": {"verbatim": False},
    "context": "Muss-Kriterium aus Protokoll"
})

# Standorte
standorte = []
for page in protokoll.get("pages", []):
    if "standort" in page.get("name", "").lower():
        for prompt in page.get("prompts", []):
            if prompt.get("type") == "multi_select":
                standorte = prompt.get("options", [])
                break

if standorte:
    questions.append({
        "id": "standort_wahl_pre_check",
        "question": "Haben Sie eine Präferenz bezüglich des Standorts, an dem Sie arbeiten möchten?",
        "type": "boolean",
        "required": True,
        "priority": 1,
        "group": "Standort",
        "category": "standort",
        "category_order": 5,
        "source": {"verbatim": False},
        "help_text": "Diese Frage hilft uns, den Dialog effizienter zu gestalten"
    })
    
    questions.append({
        "id": "standort_wahl_open",
        "question": "An welchen Standort denken Sie?",
        "type": "string",
        "required": False,
        "priority": 1,
        "group": "Standort",
        "category": "standort",
        "category_order": 5,
        "source": {"verbatim": False},
        "conditions": [{
            "when": {"field": "standort_wahl_pre_check", "op": "eq", "value": True},
            "then": {"action": "ask"}
        }],
        "context": "Fuzzy-Matching erlaubt - auch ähnliche Begriffe akzeptieren"
    })
    
    questions.append({
        "id": "standort_wahl",
        "question": f"Kein Problem. Wir haben mehrere Standorte: {', '.join(standorte[:3])}. Welcher Standort interessiert Sie am meisten?",
        "type": "choice",
        "options": standorte,
        "required": False,
        "priority": 1,
        "group": "Standort",
        "category": "standort",
        "category_order": 5,
        "source": {"verbatim": False},
        "conditions": [{
            "when": {"field": "standort_wahl_pre_check", "op": "eq", "value": False},
            "then": {"action": "ask"}
        }]
    })

# Einsatzbereiche/Abteilungen
abteilungen = []
for page in protokoll.get("pages", []):
    if "einsatz" in page.get("name", "").lower() or "abteilung" in page.get("name", "").lower():
        for prompt in page.get("prompts", []):
            if prompt.get("type") == "multi_select":
                abteilungen = prompt.get("options", [])
                break

if abteilungen:
    questions.append({
        "id": "bereich_pre_check",
        "question": "Gibt es eine bestimmte Fachabteilung, die Sie interessiert?",
        "type": "boolean",
        "required": True,
        "priority": 1,
        "group": "Einsatzbereich",
        "category": "einsatzbereiche",
        "category_order": 6,
        "source": {"verbatim": False},
        "help_text": "Diese Frage hilft uns, den Dialog effizienter zu gestalten"
    })
    
    questions.append({
        "id": "bereich_open",
        "question": "Welche Abteilung wäre das?",
        "type": "string",
        "required": False,
        "priority": 1,
        "group": "Einsatzbereich",
        "category": "einsatzbereiche",
        "category_order": 6,
        "source": {"verbatim": False},
        "conditions": [{
            "when": {"field": "bereich_pre_check", "op": "eq", "value": True},
            "then": {"action": "ask"}
        }],
        "context": "Fuzzy-Matching erlaubt - auch ähnliche Begriffe akzeptieren"
    })
    
    # Finde Prioritäten
    prios = []
    for page in protokoll.get("pages", []):
        for prompt in page.get("prompts", []):
            if "priorität" in prompt.get("question", "").lower() or "aktuell" in prompt.get("question", "").lower():
                if prompt.get("type") == "multi_select":
                    prios = prompt.get("options", [])[:2]  # Top 2
                    break
    
    frage_text = "Sehr gerne. "
    if prios:
        frage_text += f"Aktuell suchen wir besonders in {' und '.join(prios)}. "
    frage_text += "Darüber hinaus haben wir viele weitere Fachabteilungen. Was spricht Sie an?"
    
    questions.append({
        "id": "bereich",
        "question": frage_text,
        "type": "choice",
        "options": abteilungen,
        "required": False,
        "priority": 1,
        "group": "Einsatzbereich",
        "category": "einsatzbereiche",
        "category_order": 6,
        "source": {"verbatim": False},
        "conditions": [{
            "when": {"field": "bereich_pre_check", "op": "eq", "value": False},
            "then": {"action": "ask"}
        }]
    })

# Rahmenbedingungen: Arbeitszeit
questions.append({
    "id": "arbeitszeitmodell",
    "question": "Welches Arbeitszeitmodell bevorzugen Sie?",
    "type": "choice",
    "options": ["Vollzeit", "Teilzeit (flexibel)"],
    "required": True,
    "priority": 2,
    "group": "Rahmen",
    "category": "rahmenbedingungen",
    "category_order": 7,
    "source": {"verbatim": False}
})

# Rahmenbedingungen: Schichten
questions.append({
    "id": "schichten",
    "question": "Welche Schichten können Sie abdecken?",
    "type": "multi_choice",
    "options": ["Früh", "Spät", "Nacht", "Wechsel", "individuelle Anpassungen möglich"],
    "required": False,
    "priority": 2,
    "group": "Rahmen",
    "category": "rahmenbedingungen",
    "category_order": 7,
    "source": {"verbatim": False},
    "help_text": "individuelle Anpassungen möglich"
})

# Output
output = {
    "_meta": {
        "schema_version": "1.0",
        "generated_at": "2025-10-27T13:25:00.000Z",
        "generator": "python-fallback-generator@1.0.0",
        "note": "Generated via Python fallback due to TypeScript tool cache issues"
    },
    "questions": questions
}

# Speichere
output_file = Path("questions_beispiel1.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✓ questions_beispiel1.json erstellt mit {len(questions)} Fragen")
print(f"  Kategorien:")
for cat_order in range(1, 8):
    cat_questions = [q for q in questions if q.get("category_order") == cat_order]
    if cat_questions:
        cat_name = cat_questions[0].get("category", "unbekannt")
        print(f"    {cat_order}. {cat_name}: {len(cat_questions)} Frage(n)")

