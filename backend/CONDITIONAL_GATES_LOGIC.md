# Konditionale Gate-Logik für Muss-Kriterien mit Alternativen

## Problem

Wenn ein Bewerber ein Muss-Kriterium nicht erfüllt (z.B. "Studium Elektrotechnik"), aber eine Alternative haben könnte (z.B. "Ausbildung Elektriker"), würde das Gespräch zu früh beendet, ohne die Alternativen zu prüfen.

## Lösung: Gestaffelte Gate-Questions

### Struktur

```
GATE-KRITERIUM (Hauptkriterium)
├─ JA → ✅ Weiter im Gespräch
└─ NEIN → ALTERNATIVE 1 prüfen
    ├─ JA → ✅ Weiter im Gespräch
    └─ NEIN → ALTERNATIVE 2 prüfen
        ├─ JA → ✅ Weiter im Gespräch
        └─ NEIN → ❌ Gespräch höflich beenden
```

### Beispiel: Elektrotechnik-Qualifikation

**Gate-Kriterium:** Studium Elektrotechnik  
**Alternative 1:** Ausbildung Elektriker/Elektrotechniker/Elektroniker  
**Alternative 2:** Ausbildung Elektrofachkraft

## Gesprächsfluss für VoiceKI

### Szenario 1: Hauptkriterium erfüllt

```
VoiceKI: "Haben Sie ein Studium in Elektrotechnik abgeschlossen?"
Bewerber: "Ja"
VoiceKI: ✅ "Sehr gut! Dann..."
→ Weiter zu nächster Frage
```

### Szenario 2: Hauptkriterium nicht, aber Alternative 1 erfüllt

```
VoiceKI: "Haben Sie ein Studium in Elektrotechnik abgeschlossen?"
Bewerber: "Nein"
VoiceKI: "Kein Problem. Haben Sie alternativ eine Ausbildung zum Elektriker, 
         Elektrotechniker oder Elektroniker?"
Bewerber: "Ja, ich bin gelernter Elektroniker."
VoiceKI: ✅ "Ausgezeichnet! Dann..."
→ Weiter zu nächster Frage
```

### Szenario 3: Keine Alternative erfüllt

```
VoiceKI: "Haben Sie ein Studium in Elektrotechnik abgeschlossen?"
Bewerber: "Nein"
VoiceKI: "Kein Problem. Haben Sie alternativ eine Ausbildung zum Elektriker?"
Bewerber: "Nein"
VoiceKI: "Haben Sie eine Ausbildung zur Elektrofachkraft?"
Bewerber: "Nein, ich komme aus einem anderen Bereich."
VoiceKI: ❌ "Vielen Dank für Ihre Offenheit. Leider benötigen wir für diese 
         Stelle entweder ein Studium in Elektrotechnik oder eine abgeschlossene 
         Ausbildung als Elektriker/Elektrofachkraft. Deshalb müssen wir das 
         Gespräch an dieser Stelle beenden. Vielen Dank für Ihr Interesse und 
         alles Gute für Ihre weitere Suche."
→ Call beenden
```

## Implementation in questions.json

### Gate-Config Struktur

Jede Gate-Question bekommt ein `gate_config` Objekt:

```json
{
  "id": "kriterium_studium",
  "question": "Haben Sie ein Studium in Elektrotechnik abgeschlossen?",
  "type": "boolean",
  "required": true,
  "category": "standardqualifikationen",
  "gate_config": {
    "is_gate": true,
    "can_end_call": true,
    "has_alternatives": true,
    "alternative_question_ids": ["kriterium_elektriker", "kriterium_elektrofachkraft"],
    "logic": "IF studium = NEIN THEN check_alternatives ELSE continue"
  }
}
```

### Alternative Questions

```json
{
  "id": "kriterium_elektriker",
  "question": "Haben Sie alternativ eine Ausbildung zum Elektriker?",
  "type": "boolean",
  "required": false,
  "category": "standardqualifikationen",
  "conditions": [{
    "when": {"field": "kriterium_studium", "op": "eq", "value": false},
    "then": {"action": "ask"}
  }],
  "gate_config": {
    "is_alternative": true,
    "alternative_for": "kriterium_studium",
    "can_satisfy_gate": true
  }
}
```

### Finale Alternative (kann Gespräch beenden)

```json
{
  "id": "kriterium_elektrofachkraft",
  "question": "Haben Sie eine Ausbildung zur Elektrofachkraft?",
  "type": "boolean",
  "required": false,
  "category": "standardqualifikationen",
  "conditions": [
    {"when": {"field": "kriterium_studium", "op": "eq", "value": false}},
    {"when": {"field": "kriterium_elektriker", "op": "eq", "value": false}}
  ],
  "gate_config": {
    "is_alternative": true,
    "alternative_for": "kriterium_studium",
    "can_satisfy_gate": true,
    "final_alternative": true,
    "end_message_if_all_no": "Vielen Dank für Ihre Offenheit. Leider benötigen wir..."
  }
}
```

## Integration in Phase_3.md Prompt

### Ablauf-Sektion erweitern

```markdown
## 4. STANDARDQUALIFIKATIONEN - GATE (Kategorie: standardqualifikationen)

⚠️ KRITISCH: Gate-Questions - können Gespräch beenden!

### Logik für Gate-Questions MIT Alternativen:

1. **Hauptkriterium fragen**
   - Bei JA → ✅ Weiter zur nächsten Gate-Question
   - Bei NEIN → Alternative(n) prüfen

2. **Alternative(n) fragen** (nur wenn Hauptkriterium = NEIN)
   - Format: "Kein Problem. Haben Sie alternativ [Alternative]?"
   - Bei JA → ✅ Weiter (Alternative erfüllt Kriterium)
   - Bei NEIN → Nächste Alternative (falls vorhanden)

3. **Gespräch beenden** (nur wenn ALLE Alternativen = NEIN)
   - Explizit erwähnen: "Leider benötigen wir entweder [Hauptkriterium] 
     oder [Alternative 1/2/3]"
   - Höflich beenden mit Wünschen für weitere Suche

### Beispiel-Formulierungen:

**Übergang zu Alternativen:**
- "Kein Problem. Haben Sie alternativ..."
- "Alternativ würde auch... ausreichen. Haben Sie...?"

**Bei Erfüllung einer Alternative:**
- "Ausgezeichnet, das erfüllt die Anforderung!"
- "Perfekt, damit sind Sie qualifiziert!"

**Bei keiner Alternative erfüllt:**
- "Vielen Dank für Ihre Offenheit. Leider benötigen wir für diese Stelle 
   entweder [Liste aller Optionen]. Deshalb müssen wir das Gespräch an 
   dieser Stelle beenden..."
```

## Knowledge Base Format

Die Knowledge Base sollte die konditionale Logik klar darstellen:

```
======================================================================
STANDARDQUALIFIKATIONEN (GATE)
======================================================================

WICHTIG: Gate-Questions! Bei NEIN auf Muss-Kriterium → erst Alternativen 
prüfen, dann ggf. Gespräch beenden.

GATE 1: BERUFSERFAHRUNG
Typ: boolean
Pflicht: JA
Priorität: 1

Frage:
Haben Sie mindestens 2 Jahre Berufserfahrung in Deutschland?

KEINE ALTERNATIVEN
→ Bei NEIN: Gespräch beenden

------------------------------------------------------------

GATE 2: QUALIFIKATION ELEKTROTECHNIK
Typ: boolean
Pflicht: JA
Priorität: 1

Hauptkriterium:
Haben Sie ein Studium in Elektrotechnik oder verwandtem Bereich?

ALTERNATIVEN (werden bei NEIN geprüft):
  Alternative 1: Ausbildung Elektriker/Elektrotechniker/Elektroniker
  Alternative 2: Ausbildung Elektrofachkraft

LOGIK:
  IF Studium = JA → weiter
  IF Studium = NEIN:
    → Frage Alternative 1
    IF Alternative 1 = JA → weiter
    IF Alternative 1 = NEIN:
      → Frage Alternative 2
      IF Alternative 2 = JA → weiter
      IF Alternative 2 = NEIN → Gespräch beenden

ENDE-NACHRICHT:
"Leider benötigen wir entweder ein Studium in Elektrotechnik oder 
eine Ausbildung als Elektriker/Elektrofachkraft."

------------------------------------------------------------
```

## Vorteile

1. ✅ **Fairer Prozess:** Alle Qualifikationsmöglichkeiten werden geprüft
2. ✅ **Bessere Candidate Experience:** Bewerber fühlen sich gehört
3. ✅ **Höhere Erfolgsquote:** Mehr qualifizierte Kandidaten erreichen das Ende
4. ✅ **Klare Kommunikation:** Bewerber versteht, warum Gespräch endet
5. ✅ **Flexibilität:** System kann mehrere Alternativpfade abbilden

## Nächste Schritte

1. ✅ questions.json mit gate_config generiert
2. ⏳ Python Backend anpassen für konditionale Logik
3. ⏳ Knowledge Base Builder erweitern
4. ⏳ Phase_3.md mit Conditional-Gate-Logik aktualisieren
5. ⏳ ElevenLabs Prompt testen

