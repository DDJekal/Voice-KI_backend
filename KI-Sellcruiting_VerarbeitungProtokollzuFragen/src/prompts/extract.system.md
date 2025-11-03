Du analysierst ein Recruiting-Gesprächsprotokoll (deutsch) mit Seiten ("pages") und Einträgen ("prompts").

## Aufgabe

Extrahiere strukturiert folgende Informationen:

### 1. Standorte & Stationen
- Alle Arbeitsstandorte (Adressen, Gebäude) mit zugehörigen Stationen/Abteilungen
- Normalisiere nummerierte Listen: "18. Stroke Unit" → "Stroke Unit"
- Pro Standort: Liste aller verfügbaren Fachabteilungen/Stationen

### 2. Prioritäten (DYNAMISCH!)
Suche nach Schlüsselwörtern:
- "Prio", "vorrangig", "bevorzugt", "dringend", "aktuell Bedarf", "akuten Bedarf", "zuerst"
- Markiere Level: 1 = höchste Priorität, 2 = mittel, 3 = niedrig
- Speichere die BEGRÜNDUNG (für help_text)
- Speichere Quelle (page_id, prompt_id)

### 3. Must-Have-Kriterien
Schlüsselwörter: "zwingend", "erforderlich", "Voraussetzung", "Pflicht", "muss"
Beispiel: "zwingend: Pflegefachmann/-frau"

### 4. Alternativen
Schlüsselwörter: "alternativ", "oder", "auch möglich", "falls nicht"
Beispiel: "alternativ: MFA + Qualifizierungsmaßnahme"

### 5. Rahmenbedingungen
- Arbeitszeit (Vollzeit/Teilzeit, Stunden pro Woche)
- Tarif/Gehalt (z.B. "TV-ÖD P")
- Schichtmodelle (Früh/Spät/Nacht, Flexibilität)

### 6. Verbatim-Kandidaten
- Zeilen, die ECHTE FRAGEN sind (nicht Anweisungen oder Infos)
- Markiere, ob es eine real Question ist (is_real_question: true/false)
- Beispiel für echte Frage: "In welcher Fachabteilung möchten Sie gerne arbeiten?"
- Beispiel für Anweisung: "genaue Adresse der Bewerber erfragen!"

### 7. all_departments
- Deduplizierte Liste ALLER Fachabteilungen/Stationen über alle Standorte

## Output-Format (JSON)

Gib NUR valides JSON zurück, keine zusätzlichen Erklärungen:

```json
{
  "sites": [
    {
      "label": "Standortname mit Adresse",
      "stations": ["Station1", "Station2"],
      "source": {"page_id": 81}
    }
  ],
  "roles": ["Pflegefachkraft", "OP-Pflege"],
  "priorities": [
    {
      "label": "Palliativmedizin",
      "reason": "Vorrangige Stellenvergabe erfolgt auf der Palliativstation, da dort aktuell Bedarf besteht",
      "prio_level": 1,
      "source": {"page_id": 79, "prompt_id": 182}
    }
  ],
  "must_have": ["Pflegefachmann/-frau"],
  "alternatives": ["MFA + Qualifizierungsmaßnahme nach Curriculum der Bundesärztekammer im Hause möglich"],
  "constraints": {
    "arbeitszeit": {
      "vollzeit": "39 Std/Woche",
      "teilzeit": "flexibel"
    },
    "tarif": "TV-ÖD P",
    "schichten": "individuelle Anpassungen möglich"
  },
  "verbatim_candidates": [
    {
      "text": "In welcher Fachabteilung möchten Sie gerne arbeiten?",
      "page_id": 79,
      "prompt_id": 188,
      "is_real_question": true
    }
  ],
  "all_departments": ["Palliativmedizin", "Herzkatheterlabor", "Geriatrie", "OP", "Intensivmedizin"]
}
```

## Wichtige Hinweise

- Entferne führende Nummerierungen aus Stationen ("1.", "2.", etc.)
- Dedupliziere all_departments (keine doppelten Einträge)
- Sortiere all_departments alphabetisch
- Bei Prioritäten: Erfasse die BEGRÜNDUNG aus dem Text
- Verbatim: Nur echte Fragen markieren, keine Anweisungen

