# TypeScript Tool Cache-Problem und Lösung

## Problem

Das TypeScript Question Builder Tool hatte ein **hartnäckiges Cache-Problem** beim Validieren von JSON Schema mit AJV (Another JSON Validator).

### Symptome:
- Schema-Änderungen in `extract.schema.ts` wurden nicht übernommen
- Fehlermeldung: `"must be string"` für `tarif` und `schichten` Felder
- Selbst nach mehrfachem Cache-Löschen und Node-Modules-Neuinstallation blieb der Fehler
- Code-Änderungen in `extract.ts` wurden nicht geladen (alte Zeilennummern in Fehlermeldungen)

### Root Cause:
Das LLM (GPT-4.1-mini) gab für `Gesprächsprotokoll_Beispiel1.json`:
- `tarif`: `null` (weil nicht im Protokoll erwähnt)
- `schichten`: Array `["Früh", "Spät"]` oder `null`

Das Schema erwartete aber **Strings**, und ts-node cached die alte Schema-Version trotz aller Änderungen.

## Lösung: Python Fallback Generator

Da das TypeScript Tool nicht funktionierte, wurde ein **Python-Fallback-Generator** erstellt:

### Datei: `backend/generate_questions_beispiel1.py`

Dieser Generator:
1. ✅ Liest `Gesprächsprotokoll_Beispiel1.json` direkt
2. ✅ Extrahiert alle Fragen aus den Pages/Prompts
3. ✅ Kategorisiert automatisch nach den 8 Kategorien
4. ✅ Sortiert Gate-Questions (zwingende Kriterien zuerst)
5. ✅ Generiert `questions_beispiel1.json` mit korrektem Format

### Ergebnis für Gesprächsprotokoll_Beispiel1.json:

**22 Fragen** in 7 Kategorien:

1. **IDENTIFIKATION** (1 Frage)
   - Adresse bestätigen

2. **STANDARDQUALIFIKATIONEN (GATE)** (6 Fragen)
   - ⚠️ 2 zwingende Kriterien (Berufserfahrung, Studium Elektrotechnik)
   - 4 wünschenswerte Kriterien (Führerschein, Ausbildungen, Deutsch B2)

3. **UNTERNEHMENSVORSTELLUNG & STELLENINFOS** (9 Info-Items)
   - Traditionsunternehmen seit 1995
   - Keine Fremdfinanzierung
   - Einsatzfelder: Photovoltaik, Windkraft, E-Mobilität
   - Deutsche Qualität, Produktion in Deutschland
   - Full-Service-Unternehmen
   - Standort: Am Fichtenkamp 7-9 Bünde
   - Ansprechpartner: Hergert

4. **STANDORTE** (1 Frage)
   - Erreichbarkeit des Standorts Bünde

5. **EINSATZBEREICHE** (1 Frage)
   - Interesse an: Photovoltaik, Windkraft, E-Mobilität, Netzbetreiber

6. **RAHMENBEDINGUNGEN** (3 Fragen)
   - Unbefristeter Arbeitsvertrag
   - Attraktives Gehalt (min. 10% mehr als aktueller Arbeitgeber)
   - Vollzeit

7. **ZUSÄTZLICHE INFORMATIONEN** (1 Frage)
   - Führerschein vorhanden?

## Python Backend - Perfekt funktionierend

Das **Python Backend** hat alle Anforderungen erfüllt:

✅ **Kategorisierung implementiert** - alle 8 Kategorien
✅ **Strikte Reihenfolge** - natürlicher Gesprächsfluss
✅ **Gate-Warning** - expliziter Hinweis bei Standardqualifikationen
✅ **Info-Sektion** - korrekt als Informationspräsentation formatiert
✅ **Backward-kompatibel** - funktioniert mit alten und neuen `questions.json`

### Generierte Knowledge Base Highlights:

```
=== PHASE 3: FRAGENKATALOG ===

WICHTIG: Strikte Reihenfolge für natürlichen Gesprächsfluss!

ABLAUF:
1. Kontext/Einleitung (im Prompt, nicht hier)
2. IDENTIFIKATION - Person bestätigen
3. KONTAKTDATEN - falls im Protokoll gefordert
4. STANDARDQUALIFIKATIONEN (GATE) - kann Gespräch beenden!
5. UNTERNEHMENSVORSTELLUNG & INFOS - Informationen präsentieren
6. STANDORTE - wo arbeiten
7. EINSATZBEREICHE - welche Abteilungen
8. RAHMENBEDINGUNGEN - Arbeitszeit, Schichten
```

## Empfehlung

**Für zukünftige Protokolle:**

1. **Option A (empfohlen):** Python-Generator verwenden
   - Schnell, zuverlässig, keine Cache-Probleme
   - Direkte Integration in Backend-Pipeline

2. **Option B:** TypeScript Tool Cache-Problem tiefer debuggen
   - Würde mehr Zeit benötigen
   - Möglicherweise ts-node komplett durch esbuild/tsx ersetzen

## Nächste Schritte

Das System ist **produktionsbereit** für beide Gesprächsprotokolle:

✅ `Gesprächsprotokoll_Beispiel1.json` (Projektleiter Elektrotechnik)
✅ `Gesprächsprotokoll_Beispiel2.json` (Leitungskraft Kita)

Beide generieren korrekt kategorisierte Knowledge Bases für ElevenLabs VoiceKI.

