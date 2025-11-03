# Sellcruiting Question Builder (MVP)

Hybrid-Architektur zur Generierung von Fragenkatalogen aus Bewerberprofil + Gesprächsprotokoll.

## Architektur

- **Extract** (LLM): OpenAI parst das Protokoll und extrahiert dynamische Inhalte
- **Structure** (TypeScript): Deterministisches Erstellen der Basisfragen
- **Validate** (TypeScript): Regelbasierte Verarbeitung und Finalisierung

## Setup

1. **Dependencies installieren:**
   ```bash
   npm install
   ```

2. **Environment erstellen:**
   ```bash
   cp .env.example .env
   # Dann OPENAI_API_KEY in .env eintragen
   ```

3. **Ausführen:**
   ```bash
   npm start
   # oder
   npx ts-node src/index.ts
   ```

## Output

Generiert `output/questions.json` mit:
- `_meta`: Schema-Version, Timestamp, Generator
- `questions`: Array mit max. 20 Fragen (verbatim, mit Bedingungen)

## Testing

```bash
npm test
```

## Input-Dateien

Das System liest aus `Input_datein_beispiele/`:
- `Bewerberprofil_Teil1.json` (Hauptdaten)
- `Bewerberprofil_Teil2.json` (Adresse)
- `Unternehmensprofil.json` (Gesprächsprotokoll)

## Troubleshooting

**"Empty output from LLM"**: Prüfe OPENAI_API_KEY und Netzwerkverbindung

**"Protocol hat keine Seiten"**: Validiere Unternehmensprofil.json Format

**Schema-Validierung fehlgeschlagen**: Prüfe LLM-Output in Logs (LOG_LEVEL=debug)

