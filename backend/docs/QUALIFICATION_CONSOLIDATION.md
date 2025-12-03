# Qualifikations-Konsolidierung

## Problem

Bei Stellenausschreibungen mit mehreren Qualifikations-Alternativen wurden zuvor **einzelne Boolean-Fragen** für jede Qualifikation generiert:

**Vorher:**
```
- Haben Sie: Master/Bachelor Studium Psychologie? (Boolean)
- Haben Sie: Master/Bachelor Studium Sozialpädagogik? (Boolean)
- Haben Sie: Ausbildung Ergotherapeut? (Boolean)
- Haben Sie: Ausbildung Physiotherapeut? (Boolean)
- Haben Sie: Ausbildung Masseur? (Boolean)
- Haben Sie: Ausbildung Sozialarbeiter? (Boolean)
```

Dies führte zu:
- **Redundanten Fragen** → Schlechte User Experience
- **Längeren Gesprächen** → Ineffizient
- **Unnatürlichem Gesprächsfluss** → Repetitiv

## Lösung

Die neue **Qualifikations-Konsolidierung** erstellt **eine einzige Multiple-Choice-Frage** mit allen Qualifikations-Optionen:

**Nachher:**
```json
{
  "id": "qualification_degree_consolidated",
  "preamble": "Ich würde gerne Ihre Qualifikation abklären.",
  "question": "Welchen Abschluss haben Sie?",
  "type": "choice",
  "options": [
    "Master/Bachelor Studium Sozialpädagogik",
    "Ausbildung Ergotherapeut",
    "Ausbildung Physiotherapeut",
    "Ausbildung Masseur",
    "Sozialarbeiter, Suchttherapeut, Tanz-, Kunsttherapeut",
    "Anderer Abschluss"
  ],
  "required": true,
  "priority": 1,
  "group": "Qualifikation"
}
```

## Implementierung

### 1. PRE-SCAN Phase (vor allen Tiers)

Prüft **vor** der Fragen-Generierung, ob eine Konsolidierung nötig ist:

```python
# PRE-SCAN: Qualifikations-Konsolidierung prüfen
qualification_keywords = ['studium', 'abschluss', 'ausbildung', 'bachelor', 'master', 
                          'diplom', 'examen', 'zertifikat', 'qualifikation', 'fortbildung']

all_qualifications = extract_result.must_have + extract_result.alternatives
combined_text = ' '.join(all_qualifications).lower() if all_qualifications else ''

has_qualification_terms = any(keyword in combined_text for keyword in qualification_keywords)
has_multiple_options = len(all_qualifications) >= 2
qualification_consolidated = False

if has_qualification_terms and has_multiple_options:
    qualification_consolidated = True
    covered_topics.add("qualifikation_consolidated")
```

### 2. Tier 1 - Überspringen von Qualifikations-Fragen

Wenn eine Konsolidierung geplant ist, werden qualifikationsbezogene Protocol-Questions übersprungen:

```python
for pq in extract_result.protocol_questions:
    # Skip qualification questions if consolidation is planned
    if qualification_consolidated:
        question_lower = pq.text.lower()
        is_qualification_question = any(keyword in question_lower for keyword in qualification_keywords)
        
        if is_qualification_question:
            logger.debug(f"Skipping qualification question (will be consolidated): {pq.text[:60]}")
            continue
```

### 3. Tier 3 - Erstellen der konsolidierten Frage

Erstellt die Multiple-Choice-Frage mit bereinigten Optionen:

```python
if qualification_consolidated and "qualifikation" not in covered_topics:
    # Bereinige Optionen (entferne "Zwingend:", "Alternativ:", etc.)
    cleaned_options = []
    for qual in all_qualifications:
        cleaned = re.sub(r'^(zwingend|alternativ|wünschenswert|bevorzugt):\s*', '', qual, flags=re.I)
        cleaned = cleaned.strip()
        if cleaned and cleaned not in cleaned_options:
            cleaned_options.append(cleaned)
    
    # Füge Fallback-Option hinzu
    if "anderer" not in combined_text.lower():
        cleaned_options.append("Anderer Abschluss")
    
    # Erstelle konsolidierte Frage
    questions.append(Question(
        id="qualification_degree_consolidated",
        preamble="Ich würde gerne Ihre Qualifikation abklären." if len(cleaned_options) > 3 else None,
        question="Welchen Abschluss haben Sie?",
        type=QuestionType.CHOICE,
        options=cleaned_options,
        required=True,
        priority=1,
        group=QuestionGroup.QUALIFIKATION
    ))
    
    # Markiere alle als covered
    covered_topics.add("qualifikation")
    for qual in all_qualifications:
        covered_topics.add(_slugify(qual))
```

## Ergebnis

**Vorher:**
- 11 Qualifikations-Fragen (10x Boolean + 1x Deutschkenntnisse)
- 25 Fragen gesamt

**Nachher:**
- 2 Qualifikations-Fragen (1x konsolidierte Choice + 1x Deutschkenntnisse)
- 13 Fragen gesamt

**Reduzierung:** -9 redundante Fragen = **~47% weniger Fragen** in diesem Bereich! ✅

## Vorteile

1. ✅ **Bessere UX:** Eine klare Auswahl statt vieler Ja/Nein-Fragen
2. ✅ **Natürlicher Gesprächsfluss:** "Welchen Abschluss haben Sie?"
3. ✅ **Effizienter:** Weniger Fragen, schnellere Gespräche
4. ✅ **Flexibel:** "Anderer Abschluss" als Fallback
5. ✅ **Smart:** Automatische Erkennung von Qualifikations-Alternativen

## Dateien geändert

- `backend/src/questions/pipeline/structure.py`: PRE-SCAN + Konsolidierungs-Logik
- `backend/test_protocol_qualifications.json`: Testdatei für Qualifikations-Konsolidierung

