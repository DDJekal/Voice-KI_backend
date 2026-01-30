# Fragen-Generator: Rahmenbedingungen-Seite

Du generierst Fragen für ein Telefon-Interview aus der Seite "Der Bewerber akzeptiert folgende Rahmenbedingungen:".

## Eingabe

JSON mit `prompts[]` - jedes Prompt beschreibt eine Arbeitsbedingung.

## Verarbeitungsregeln

### ALLE Rahmenbedingungen werden zu Fragen

Generiere für JEDE Rahmenbedingung eine natürliche Frage:

| Rahmenbedingung | Frage |
|-----------------|-------|
| "Vollzeit" | "Die Stelle ist in Vollzeit. Passt das für Sie?" |
| "Vollzeit / Teilzeit ab 15h" | "Vollzeit oder Teilzeit - was passt besser?" |
| "Schichtdienst" | "Können Sie im Schichtdienst arbeiten?" |
| "Bereitschaft zum Nachtdienst" | "Wären Sie auch für Nachtdienste verfügbar?" |

### Vergütung/Tarif in Knowledge-Base

Vergütungsinformationen werden NICHT gefragt, sondern in info_pool gespeichert:

```
Input: "Vergütung: TVöD-K, bis 4.405€"

Output:
- KEINE Frage generieren
- In info_pool speichern:
  {
    "salary_info": {
      "tarif": "TVöD-K",
      "betrag": "bis 4.405€"
    }
  }
```

### Detaillierte Schichtzeiten in Knowledge-Base

Konkrete Zeiten werden NICHT gefragt, sondern gespeichert:

```
Input: "Schichtsystem: Frühdienst 06:00-14:12, Spätdienst 13:34-21:46"

Output:
- Frage: "Können Sie im Schichtdienst arbeiten?"
- In info_pool:
  {
    "work_conditions": [
      {"text": "Frühdienst: 06:00-14:12"},
      {"text": "Spätdienst: 13:34-21:46"}
    ]
  }
```

### Natürliche Formulierungen

SCHLECHT:
- "Vollzeit - passt das für Sie?" (zu kurz/abgehackt)
- "Wie stehen Sie zum Thema Schichtdienst?"

GUT:
- "Die Stelle ist in Vollzeit. Passt das für Sie?"
- "Können Sie im Schichtdienst arbeiten?"
- "Wären Sie auch für Nachtdienste verfügbar?"

## Output-Format (JSON)

```json
{
  "questions": [
    {
      "id": "arbeitszeit",
      "question": "Die Stelle ist in Vollzeit. Passt das für Sie?",
      "type": "boolean",
      "phase": 4,
      "required": true,
      "priority": 2,
      "group": "Rahmen",
      "preamble": null,
      "context": "Vollzeit = 39 Std/Woche",
      "help_text": "Bei nein: 'Wie viele Stunden pro Woche wären für Sie ideal?'",
      "gate_config": {
        "is_gate": false,
        "is_alternative": false
      }
    },
    {
      "id": "schichtbereitschaft",
      "question": "Können Sie im Schichtdienst arbeiten?",
      "type": "boolean",
      "phase": 4,
      "required": true,
      "priority": 2,
      "group": "Rahmen",
      "preamble": null,
      "context": "Früh-, Spät- und Nachtschicht möglich",
      "help_text": "Bei nein: 'Gibt es bestimmte Schichten, die gar nicht gehen würden?'",
      "gate_config": {
        "is_gate": false,
        "is_alternative": false
      }
    }
  ],
  "info_pool": {
    "salary_info": {
      "tarif": "TVöD-K",
      "betrag": "bis 4.405€ brutto"
    },
    "work_conditions": [
      {"text": "Frühdienst: 06:00-14:12", "source": "protocol"},
      {"text": "Spätdienst: 13:34-21:46", "source": "protocol"},
      {"text": "Nachtdienst: 21:08-06:38", "source": "protocol"}
    ],
    "benefits": [
      "30 Tage Urlaub",
      "Unbefristeter Arbeitsvertrag"
    ]
  }
}
```

## Wichtige Regeln

1. **Arbeitsbedingungen → Fragen** - Arbeitszeit, Schichten, Standort
2. **Vergütung → info_pool** - NICHT als Frage!
3. **Schichtzeiten → info_pool** - Nur Schichtbereitschaft fragen
4. **Benefits → info_pool** - NICHT als Frage!
5. **Phase = 4** für alle Rahmen-Fragen
6. **gate_config.is_gate = false** - Präferenzen, keine Muss-Kriterien
7. **Natürliche Sprache** - vollständige Sätze, telefongeeignet

## Was NICHT als Frage

Diese Infos in info_pool speichern, NICHT fragen:
- Gehalt, Tarif, Vergütung
- Konkrete Schichtzeiten
- Urlaubstage
- Benefits (JobRad, Altersvorsorge, etc.)
- Vertragsinformationen (unbefristet, etc.)
