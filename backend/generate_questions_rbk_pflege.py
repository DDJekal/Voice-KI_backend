"""
Generiere questions.json für RBK Pflegefachkräfte (Gesprächsprotokoll_Teil3.json)
mit konditionaler Gate-Logik
"""
import json
from pathlib import Path

# Lade Gesprächsprotokoll_Teil3 (jetzt RBK Pflege)
input_file = Path("../Input_ordner/Gesprächsprotokoll_Teil3.json")
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

#2. STANDARDQUALIFIKATIONEN (GATE)

# Gate 1: Pflegefachkraft (zwingend, KEINE Alternativen)
questions.append({
    "id": "kriterium_pflegefachkraft",
    "question": "Sind Sie examinierte Pflegefachfrau oder Pflegefachmann?",
    "type": "boolean",
    "required": True,
    "priority": 1,
    "group": "Qualifikation",
    "category": "standardqualifikationen",
    "category_order": 3,
    "source": {
        "page_id": 79,
        "prompt_id": 184,
        "verbatim": True
    },
    "context": "Muss-Kriterium",
    "gate_config": {
        "is_gate": True,
        "can_end_call": True,
        "has_alternatives": True,
        "alternative_question_ids": ["kriterium_mfa_op"],
        "logic": "IF Pflegefachkraft = NEIN AND MFA = NEIN THEN end_call"
    }
})

# Alternative: MFA für OP-Bereich
questions.append({
    "id": "kriterium_mfa_op",
    "question": "Für den OP-Bereich haben wir eine Alternative: Sind Sie MFA (Medizinische Fachangestellte) und interessiert an einer Qualifizierungsmaßnahme nach Curriculum der Bundesärztekammer?",
    "type": "boolean",
    "required": False,
    "priority": 1,
    "group": "Qualifikation",
    "category": "standardqualifikationen",
    "category_order": 3,
    "source": {
        "page_id": 79,
        "prompt_id": 186,
        "verbatim": True
    },
    "context": "Alternative für OP-Bereich",
    "conditions": [{
        "when": {"field": "kriterium_pflegefachkraft", "op": "eq", "value": False},
        "then": {"action": "ask"}
    }],
    "gate_config": {
        "is_alternative": True,
        "alternative_for": "kriterium_pflegefachkraft",
        "can_satisfy_gate": True,
        "final_alternative": True,
        "end_message_if_all_no": "Vielen Dank für Ihre Offenheit. Leider benötigen wir für diese Stelle entweder eine examinierte Pflegefachkraft oder eine MFA mit Interesse an einer Qualifizierungsmaßnahme für den OP-Bereich. Deshalb müssen wir das Gespräch an dieser Stelle beenden. Vielen Dank für Ihr Interesse und alles Gute für Ihre weitere Suche."
    }
})

# 3. INFO - Palliativstation Priorität
questions.append({
    "id": "info_prio_palliativ",
    "question": "Wichtig: Vorrangige Stellenvergabe erfolgt auf der Palliativstation, da dort aktuell Bedarf besteht. Falls diese Station nicht infrage kommt, prüfen wir gerne alternative Einsatzmöglichkeiten in anderen Bereichen",
    "type": "info",
    "required": False,
    "priority": 1,
    "group": "Info",
    "category": "info",
    "category_order": 4,
    "source": {
        "page_id": 79,
        "prompt_id": 182,
        "verbatim": True
    }
})

# 4. EINSATZBEREICHE - Welche Fachabteilung?
# Lese alle Abteilungen aus den Pages
abteilungen = []
for page in protokoll.get("pages", []):
    for prompt in page.get("prompts", []):
        if "fachabteilung" in prompt.get("question", "").lower():
            # Suche nach multi_select mit Abteilungen
            if prompt.get("type") == "multi_select" and prompt.get("options"):
                abteilungen = prompt.get("options", [])
                break

# Falls keine explizite Liste, erstelle Standard-Liste
if not abteilungen:
    abteilungen = [
        "Palliativstation",
        "OP",
        "Intensivstation",
        "Notaufnahme",
        "Innere Medizin",
        "Chirurgie",
        "Geriatrie"
    ]

questions.append({
    "id": "einsatzbereich_interesse",
    "question": "In welcher Fachabteilung möchten Sie gerne arbeiten?",
    "type": "choice",
    "options": abteilungen,
    "required": True,
    "priority": 1,
    "group": "Einsatzbereich",
    "category": "einsatzbereiche",
    "category_order": 6,
    "source": {
        "page_id": 79,
        "prompt_id": 188,
        "verbatim": True
    },
    "help_text": "Vorrangige Vergabe: Palliativstation"
})

# 5. RAHMENBEDINGUNGEN
questions.append({
    "id": "arbeitszeitmodell",
    "question": "Welches Arbeitszeitmodell bevorzugen Sie?",
    "type": "choice",
    "options": ["Vollzeit (39 Std/Woche)", "Teilzeit (flexibel)"],
    "required": True,
    "priority": 2,
    "group": "Rahmen",
    "category": "rahmenbedingungen",
    "category_order": 7,
    "source": {
        "page_id": 80,
        "prompt_id": 194,
        "verbatim": True
    }
})

questions.append({
    "id": "verguetung_info",
    "question": "Die Vergütung ist angelehnt an den TV-ÖD P. Ist das für Sie grundsätzlich in Ordnung?",
    "type": "boolean",
    "required": False,
    "priority": 3,
    "group": "Rahmen",
    "category": "rahmenbedingungen",
    "category_order": 7,
    "source": {
        "page_id": 80,
        "prompt_id": 198,
        "verbatim": True
    }
})

# 6. KONTAKTDATEN - Adresse erfragen
questions.append({
    "id": "adresse_erfragen",
    "question": "Können Sie mir Ihre vollständige Adresse nennen?",
    "type": "string",
    "required": True,
    "priority": 1,
    "group": "Kontakt",
    "category": "kontaktinformationen",
    "category_order": 2,
    "source": {
        "page_id": 79,
        "prompt_id": 190,
        "verbatim": True
    },
    "context": "Falls noch nicht vollständig bekannt"
})

# Output
output = {
    "_meta": {
        "schema_version": "1.1",
        "generated_at": "2025-10-27T14:00:00.000Z",
        "generator": "python-rbk-pflege-generator@1.0.0",
        "source": "Gesprächsprotokoll_Teil3.json",
        "note": "Robert Bosch Klinikum Pflegefachkräfte mit konditionaler Gate-Logik",
        "features": ["conditional_gates", "alternative_checks"]
    },
    "questions": questions
}

# Speichere
output_file = Path("questions_rbk_pflege.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✅ questions_rbk_pflege.json erstellt mit {len(questions)} Fragen")
print(f"\n📊 Kategorien:")
for cat_order in range(1, 9):
    cat_questions = [q for q in questions if q.get("category_order") == cat_order]
    if cat_questions:
        cat_name = cat_questions[0].get("category", "unbekannt")
        print(f"   {cat_order}. {cat_name.upper()}: {len(cat_questions)} Frage(n)")

print(f"\n💡 Gate-Logik:")
print(f"   Gate: Pflegefachkraft (mit Alternative)")
print(f"     → Alternative: MFA für OP-Bereich")
print(f"     → Bei BEIDEN NEIN: Gespräch beenden")

