# Campaign Setup Guide - Phase 1

**Letzte Aktualisierung:** November 3, 2025  
**Phase:** 1 von 2 (Setup)

---

## Überblick

Das Campaign Setup Tool erstellt **einmalig pro Campaign** ein wiederverwendbares Package mit KB Templates und Metadaten. Dieses Package kann dann für **alle Bewerber** dieser Campaign genutzt werden, ohne jedes Mal neu generieren zu müssen.

---

## Workflow

```
1. User generiert questions.json (TypeScript Tool)
   ↓
2. User führt Setup aus: python setup_campaign.py --campaign-id 16
   ↓
3. Tool lädt Daten aus Cloud-API
   ↓
4. Templates werden mit {{Platzhaltern}} erstellt
   ↓
5. Package wird lokal gespeichert: campaign_packages/16.json
   ↓
6. Bereit für Phase 2: Link-Generierung
```

---

## Voraussetzungen

### 1. questions.json generieren

```bash
cd ../KI-Sellcruiting_VerarbeitungProtokollzuFragen
npm run generate
```

**Output:** `output/questions.json`

### 2. .env konfigurieren

```env
# API Data Source aktivieren
USE_API_SOURCE=true

# Production API
API_URL=https://high-office.hirings.cloud/api/v1
API_KEY=your_api_key_here

# ElevenLabs (für später - Phase 2)
ELEVENLABS_API_KEY=sk_your_key_here
ELEVENLABS_AGENT_ID=agent_your_id_here
```

### 3. Python Environment

```bash
cd backend
source venv/bin/activate  # Linux/Mac
# ODER
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

---

## Verwendung

### Setup für Campaign durchführen

```bash
cd backend
python setup_campaign.py --campaign-id 16
```

**Output:**
```
======================================================================
🔧 CAMPAIGN SETUP - Phase 1
======================================================================
Campaign ID: 16
======================================================================

📡 Initialisiere API Data Source...
   ✅ API URL: https://high-office.hirings.cloud/api/v1

🏗️  Initialisiere Package Builder...
   ✅ Prompts Dir: ../VoiceKI _prompts
   ✅ Questions Path: ../KI-Sellcruiting_VerarbeitungProtokollzuFragen/output/questions.json

======================================================================
🔧 Erstelle Campaign Package für Campaign 16
1️⃣ Lade questions.json...
   ✅ 15 Fragen geladen
2️⃣ Lade Company & Campaign Daten von API...
   ✅ Company: Robert Bosch Krankenhaus
   ✅ Campaign: Pflegefachkräfte
3️⃣ Extrahiere Prioritäten...
   ✅ Prioritäten: Palliativ, Herzkatheter
4️⃣ Erstelle KB Templates...
   ✅ Phase 1: 2500 Zeichen
   ✅ Phase 2: 1800 Zeichen
   ✅ Phase 3: 8500 Zeichen
   ✅ Phase 4: 1200 Zeichen
5️⃣ Stelle Package zusammen...
   ✅ Package validiert
======================================================================

💾 Speichere Package...
💾 Package gespeichert: backend/campaign_packages/16.json

======================================================================
✅ CAMPAIGN SETUP ABGESCHLOSSEN!
======================================================================
📦 Package: backend/campaign_packages/16.json
🏢 Company: Robert Bosch Krankenhaus
📋 Campaign: Pflegefachkräfte
❓ Fragen: 15
📄 Templates: 4 Phasen
======================================================================

🔗 Bereit für Phase 2: Link-Generierung
   python generate_link.py --applicant-id <ID> --campaign-id 16
```

---

### Alle Campaigns auflisten

```bash
python setup_campaign.py --list
```

**Output:**
```
======================================================================
📦 GESPEICHERTE CAMPAIGN PACKAGES (2)
======================================================================

Campaign ID: 16
  Company: Robert Bosch Krankenhaus
  Campaign: Pflegefachkräfte
  Erstellt: 2025-11-03T10:30:00Z
  Datei: backend/campaign_packages/16.json

Campaign ID: 36
  Company: Petersen Inc
  Campaign: Leitungskraft Kita
  Erstellt: 2025-11-03T11:00:00Z
  Datei: backend/campaign_packages/36.json
```

---

### Package überschreiben

```bash
python setup_campaign.py --campaign-id 16 --force
```

**Wann nötig:**
- Unternehmensdaten haben sich geändert
- questions.json wurde aktualisiert
- Templates sollen neu generiert werden

---

## Package-Struktur

### Campaign Package (JSON)

```json
{
  "campaign_id": "16",
  "company_name": "Robert Bosch Krankenhaus",
  "campaign_name": "Pflegefachkräfte",
  "created_at": "2025-11-03T10:30:00Z",
  
  "questions": {
    "questions": [...]
  },
  
  "kb_templates": {
    "phase_1": "PHASE 1...\nName: {{first_name}} {{last_name}}...",
    "phase_2": "PHASE 2...\nUnternehmen: Robert Bosch...",
    "phase_3": "PHASE 3...\nFragenkatalog...",
    "phase_4": "PHASE 4...\nBewerber: {{first_name}}..."
  },
  
  "meta": {
    "company_size": "3420",
    "company_address": "Auerbachstraße 110...",
    "company_benefits": "attraktive Vergütung...",
    "priority_areas": ["Palliativ", "Herzkatheter"],
    "career_page": "https://karriere.rbk.de/"
  }
}
```

---

## Variablen-Platzhalter

### Bewerber-Variablen (Phase 2)

Werden später mit echten Bewerberdaten gefüllt:

```
{{first_name}}          - Vorname
{{last_name}}           - Nachname
{{telephone}}           - Telefonnummer
{{email}}               - Email-Adresse
{{street}}              - Straße
{{house_number}}        - Hausnummer
{{postal_code}}         - Postleitzahl
{{city}}                - Stadt
```

### Company-Variablen (fix)

Werden direkt im Setup eingebettet:

```
{{companyname}}         - Firmenname (direkt eingebettet)
{{companysize}}         - Mitarbeiterzahl (direkt eingebettet)
{{companypitch}}        - Benefits (direkt eingebettet)
{{campaignrole_title}}  - Stellenbezeichnung (Phase 2 Injektion)
{{campaignlocation}}    - Standort (Phase 2 Injektion)
```

---

## Troubleshooting

### Problem: "questions.json nicht gefunden"

**Ursache:** TypeScript Tool wurde nicht ausgeführt

**Lösung:**
```bash
cd ../KI-Sellcruiting_VerarbeitungProtokollzuFragen
npm run generate
```

---

### Problem: "USE_API_SOURCE muss auf 'true' gesetzt sein"

**Ursache:** API-Modus nicht aktiviert

**Lösung:** In `.env` setzen:
```env
USE_API_SOURCE=true
```

---

### Problem: "Campaign X nicht gefunden"

**Ursache:** Campaign ID existiert nicht in API

**Lösung:**
- Prüfe Campaign ID im Backend/Dashboard
- Liste verfügbare Campaigns

---

### Problem: "Package existiert bereits"

**Ursache:** Setup wurde bereits durchgeführt

**Optionen:**
1. Package nutzen: Phase 2 starten
2. Package überschreiben: `--force` Flag nutzen

---

## Nächste Schritte

Nach erfolgreichem Setup:

### Option A: Einzelnen Link generieren
```bash
python generate_link.py --applicant-id "+49 123..." --campaign-id 16
```

### Option B: Batch-Link-Generierung
```bash
python batch_generate_links.py --campaign-id 16
```

**Siehe:** `LINK_GENERATION.md` (Phase 2 Dokumentation)

---

## Technische Details

### Komponenten

1. **TemplateBuilder** (`src/campaign/template_builder.py`)
   - Erstellt KB Templates mit {{Platzhaltern}}
   - Nutzt Phase-Prompts aus `VoiceKI _prompts/`
   - 4 Templates für 4 Phasen

2. **CampaignPackageBuilder** (`src/campaign/package_builder.py`)
   - Orchestriert Template-Erstellung
   - Lädt Daten von API
   - Validiert Package

3. **CampaignStorage** (`src/storage/campaign_storage.py`)
   - Speichert Packages als JSON
   - Lädt Packages
   - Verwaltet campaign_packages/ Ordner

4. **setup_campaign.py** (CLI-Tool)
   - Argparse für CLI
   - Integration aller Komponenten
   - Error Handling

---

### Ordnerstruktur

```
backend/
├── setup_campaign.py                   # CLI-Tool (Phase 1)
├── campaign_packages/                  # Lokale Packages
│   ├── 16.json
│   └── 36.json
├── src/
│   ├── campaign/
│   │   ├── template_builder.py
│   │   └── package_builder.py
│   └── storage/
│       └── campaign_storage.py
└── docs/
    └── CAMPAIGN_SETUP.md              # Diese Datei
```

---

## Best Practices

### 1. Setup nur einmal pro Campaign

Campaign Setup ist **einmalig**. Packages sind wiederverwendbar für alle Bewerber dieser Campaign.

### 2. Setup bei Änderungen neu durchführen

Führe Setup neu aus (mit `--force`) wenn:
- Unternehmensdaten sich ändern
- questions.json aktualisiert wurde
- Phase-Prompts angepasst wurden

### 3. Packages in Version Control?

**NEIN** - Packages sind generiert und können jederzeit neu erstellt werden.

Füge zu `.gitignore` hinzu:
```
campaign_packages/
```

### 4. Backup vor --force

```bash
cp campaign_packages/16.json campaign_packages/16_backup.json
python setup_campaign.py --campaign-id 16 --force
```

---

## FAQ

**Q: Muss ich für jeden Bewerber Setup durchführen?**  
A: Nein! Setup ist einmalig pro Campaign. Alle Bewerber nutzen dasselbe Package.

**Q: Wie oft muss ich Setup durchführen?**  
A: Nur einmal pro Campaign oder bei Änderungen an Company/Questions.

**Q: Kann ich Packages teilen?**  
A: Ja, JSON-Dateien können geteilt werden. Aber besser über Cloud-API (Phase 3).

**Q: Was passiert bei fehlender Adresse?**  
A: Adresse wird basierend auf Gesprächsprotokoll behandelt. Templates enthalten beide Varianten.

**Q: Funktioniert ohne API?**  
A: Nein, API ist Pflicht für Company/Campaign Daten. Nur File-Source ist nicht ausreichend.

---

**Version:** 1.0  
**Phase:** 1 von 2  
**Nächste Phase:** Link-Generierung (siehe LINK_GENERATION.md)  
**Status:** Production Ready

