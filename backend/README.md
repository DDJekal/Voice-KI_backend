# VoiceKI Backend

Standalone Python Orchestrator für ElevenLabs Voice-Recruiting-Calls.

## 🆕 **Update Oktober 2025: Neue Input-Struktur unterstützt!**

Das Backend wurde erweitert und unterstützt jetzt **beide Datenstrukturen**:

### **Neue Struktur (echte Cloud-Daten):**
```
Input_ordner/
├── Bewerberprofil.json                    # Eine Datei
├── Adresse des Bewerbers.json             # Separate Adresse
├── Unternehmensprofil.json                # Q&A Format (question/answer)
└── Gesprächsprotokoll.json                # Separates Protokoll
```

### **Alte Struktur (Test-Daten, backward compatible):**
```
Input_datein_beispiele/
├── Bewerberprofil_Teil1.json
├── Bewerberprofil_Teil2.json
└── Unternehmensprofil.json
```

**Beide funktionieren gleichzeitig!** Das Backend erkennt automatisch das Format.

---

## Features

- ✅ Lädt Bewerber- und Unternehmensdaten aus JSON-Dateien
- ✅ **NEU:** Unterstützt Q&A Format mit question/answer Paaren
- ✅ **NEU:** Automatische Format-Erkennung
- ✅ Integriert TypeScript Question Builder Tool
- ✅ Aggregiert Daten für Phase 1-4
- ✅ Erstellt Voice-optimierte Knowledge Bases
- ✅ Startet ElevenLabs Conversational AI Calls
- ✅ Modular aufgebaut für spätere Cloud-Integration
- ✅ Backward-compatible mit alten Test-Daten

---

## Setup

### 1. Dependencies installieren

```bash
# Virtual Environment erstellen
python -m venv venv

# Dependencies installieren
venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Konfiguration erstellen (optional)

```bash
cp .env.example .env
```

Dann in `.env` eintragen:
- `ELEVENLABS_API_KEY`: Dein ElevenLabs API Key
- `ELEVENLABS_AGENT_ID`: Deine Agent ID
- `DATA_DIR`: Pfad zu den JSON-Dateien

### 3. Tests ausführen

#### **Test mit neuer Struktur:**
```bash
venv\Scripts\python.exe test_new_structure.py
```

#### **Test mit alter Struktur:**
```bash
venv\Scripts\python.exe test_backend.py
```

**Ergebnis:**
```
✅ ALLE TESTS BESTANDEN!
✓ Neue Input-Struktur funktioniert
✓ Q&A Format wird korrekt geparst
✓ Backward Compatibility gewahrt
```

---

## Verwendung

### Mit neuer Struktur (Input_ordner/)

```bash
venv\Scripts\python.exe main.py \
  --applicant-id test \
  --campaign-id test \
  --data-dir ../Input_ordner \
  --dry-run
```

**Output:**
```
Unternehmen: Robert Bosch Krankenhaus GmbH
Größe: 3.420 Mitarbeitende
Standort: Auerbachstraße 110, 70376 Stuttgart
Knowledge Base: 9.537 Zeichen
```

### Mit alter Struktur (backward compatible)

```bash
venv\Scripts\python.exe main.py \
  --applicant-id test \
  --campaign-id test \
  --data-dir ../KI-Sellcruiting_VerarbeitungProtokollzuFragen/Input_datein_beispiele \
  --dry-run
```

### Produktiv (mit echtem ElevenLabs)

```bash
# Ohne --dry-run Flag
venv\Scripts\python.exe main.py \
  --applicant-id 15 \
  --campaign-id 26 \
  --data-dir ../Input_ordner
```

## Architektur

```
backend/
├── src/
│   ├── data_sources/       # Datenquellen (File, API)
│   ├── aggregator/         # Datenaggregation & Transformation
│   ├── elevenlabs/         # ElevenLabs API Client
│   ├── orchestrator/       # Call-Orchestrierung
│   └── config.py           # Konfiguration
│
├── main.py                 # CLI Entry Point
├── requirements.txt
└── .env                    # Konfiguration (nicht in Git)
```

## Workflow

1. **Daten laden** → FileDataSource lädt JSON-Files
2. **Questions.json** → Optional TypeScript Tool ausführen
3. **Aggregation** → UnifiedAggregator extrahiert Variablen
4. **Knowledge Base** → KnowledgeBaseBuilder erstellt Text für ElevenLabs
5. **ElevenLabs Call** → VoiceClient startet Conversation

## Development

### Dry-Run Mode

Für Tests ohne echte API-Calls:

```bash
python main.py --applicant-id test --campaign-id test --dry-run
```

Der Mock-Client simuliert ElevenLabs-Verhalten und gibt Debug-Output.

### Eigene Data Source

Um eine API-basierte Data Source zu verwenden:

1. Implementiere `DataSource` Interface in `src/data_sources/`
2. Übergebe in `main.py` statt `FileDataSource`

### TypeScript Tool Integration

Das Tool wird automatisch aufgerufen wenn:
- `--generate-questions` Flag gesetzt ist
- Oder `GENERATE_QUESTIONS=true` in .env

## Troubleshooting

**"ELEVENLABS_API_KEY nicht gesetzt"**
→ Prüfe `.env` Datei

**"Datei nicht gefunden"**
→ Prüfe `DATA_DIR` in `.env` oder `--data-dir` Parameter

**"TypeScript Tool fehlgeschlagen"**
→ Prüfe ob `npm install` im Tool-Verzeichnis ausgeführt wurde

## Next Steps

- [ ] Cloud API Integration (statt FileLoader)
- [ ] Phase-Transitions (separate Calls pro Phase)
- [ ] Webhook für Call-Completion
- [ ] Transkript-Verarbeitung & Speicherung
- [ ] FastAPI Wrapper für REST API

