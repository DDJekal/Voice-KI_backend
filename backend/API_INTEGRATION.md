# API Integration - VoiceKI Backend

**Datum:** November 2025  
**Status:** ✅ IMPLEMENTIERT

---

## Überblick

Das VoiceKI Backend unterstützt jetzt zwei Datenquellen:
1. **File-based:** Lädt Daten aus lokalen JSON-Dateien (für Tests)
2. **API-based:** Lädt Daten von der Cloud-API (für Produktion)

Die API-Integration ermöglicht es, automatisch alle Bewerber mit Status "Neu intern" zu verarbeiten und Calls zu starten.

---

## API-Struktur

### Endpoints

**Base URL:** `https://high-office.hirings.cloud/api/v1`

#### Neue Bewerber
```
GET /applicants/new
```
Gibt alle Bewerber mit Status "Neu intern" zurück.

#### Nicht erreichte Bewerber
```
GET /applicants/not_reached
```
Gibt alle Bewerber zurück, die beim ersten Versuch nicht erreicht wurden.

### ⚠️ Test-Bewerber

Die API enthält Test-Bewerber vom Delivering-Team für Zapier-Tests.

**Erkennungsmerkmal:** Diese haben **"Test"** im Vor- oder Nachnamen.

**Automatische Filterung:** Das System filtert diese standardmäßig heraus!

Beispiele:
- `Max Test`
- `Test Schmidt` 
- `Jessica Testmann`

### Response Format
```json
{
    "applicants": [
        {
            "first_name": "Jessica",
            "last_name": "Niewalda",
            "telephone": "+49 1234 56789",
            "campaign_id": 16
        }
    ],
    "companies": [
        {
            "id": 2,
            "name": "Robert Bosch Krankenhaus GmbH",
            "onboarding": {
                "pages": [
                    {
                        "prompts": [
                            {
                                "question": "Wie viele Mitarbeitende?",
                                "answer": "3420"
                            }
                        ]
                    }
                ]
            }
        }
    ],
    "campaigns": [
        {
            "id": 16,
            "name": "Pflegefachkräfte",
            "company_id": 2,
            "transcript": {
                "pages": [
                    {
                        "prompts": [
                            {
                                "question": "Zwingend: Pflegefachkraft",
                                "position": 1
                            }
                        ]
                    }
                ]
            }
        }
    ]
}
```

---

## Transformation

Die API-Daten werden automatisch ins erwartete Format transformiert:

### Bewerber (Applicant)
**API-Format → System-Format:**
```python
{
    "first_name": "Jessica",
    "last_name": "Niewalda",
    "telephone": "+49 1234 56789",
    "campaign_id": 16
}
# →
{
    "first_name": "Jessica",
    "last_name": "Niewalda",
    "telephone": "+49 1234 56789",
    "email": "",
    "campaign_id": 16
}
```

### Adresse
**Besonderheit:** Adresse ist NICHT in der API enthalten und wird im Gespräch (Phase 1) erfragt.

```python
# API gibt zurück:
{
    "street": "",
    "house_number": "",
    "postal_code": "",
    "city": ""
}
```

### Unternehmen (Company)
**Transformation:**
- Extrahiert Antworten aus Onboarding-Prompts
- Mapped anhand von Keywords in Questions

```python
# API: pages → prompts → question/answer
# System: flache Struktur mit extrahierten Werten

{
    "name": "Robert Bosch Krankenhaus",
    "size": "3420",  # extrahiert aus "Wie viele Mitarbeitende"
    "address": "Auerbachstraße 110...",  # extrahiert aus "Adresse"
    "benefits": "attraktive Vergütung...",  # extrahiert aus "Was unterscheidet"
}
```

### Gesprächsprotokoll (Campaign Transcript)
**Direkte Übernahme** (bereits im richtigen Format):
```python
{
    "id": 16,
    "name": "Pflegefachkräfte",
    "pages": [...]  # direkt übernommen
}
```

---

## Konfiguration

### 1. Environment Variables (.env)

```env
# API Data Source aktivieren
USE_API_SOURCE=true

# API Credentials
API_URL=https://high-office.hirings.cloud/api/v1
API_KEY=your_api_key_here

# Bewerber-Status: "new" oder "not_reached"
API_STATUS=new

# Test-Bewerber automatisch filtern (empfohlen)
FILTER_TEST_APPLICANTS=true

# ElevenLabs (weiterhin erforderlich)
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_AGENT_ID=agent_...
```

### 2. Umschalten zwischen File und API

**File-based (für Tests):**
```env
USE_API_SOURCE=false
DATA_DIR=../Input_ordner
```

**API-based (für Produktion):**
```env
USE_API_SOURCE=true
API_URL=https://high-office.hirings.cloud/api/v1
API_KEY=your_key
API_STATUS=new
FILTER_TEST_APPLICANTS=true
```

---

## Verwendung

### 1. Einzelnen Bewerber verarbeiten

```bash
cd backend

# Mit API-Daten
USE_API_SOURCE=true python main.py \
  --applicant-id "+49 1234 56789" \
  --campaign-id "16"
```

### 2. Alle Bewerber verarbeiten (Batch)

```bash
cd backend
python process_all_applicants.py
```

**Was passiert:**
1. Lädt alle Bewerber mit Status "Neu intern"
2. Startet für jeden einen Call
3. Zeigt Fortschritt und Fehler
4. Gibt Zusammenfassung aus

**Output:**
```
[1/5] Verarbeite: Jessica Niewalda
             Telefon: +49 1234 56789
             Campaign ID: 16
   ✅ Call gestartet: webrtc_1234567890

...

ZUSAMMENFASSUNG
✅ Erfolgreich: 4
❌ Fehlgeschlagen: 1
📊 Gesamt: 5
```

### 3. API-Verbindung testen

```bash
cd backend
python test_api_source.py
```

Gibt interaktiven Test aus, der alle Transformationen prüft.

---

## Caching

Die API-Daten werden **einmalig pro Session** geladen und gecacht:

```python
api = APIDataSource(api_url, api_key)

# 1. Call: API-Request
applicants = api.list_pending_applicants()  # → HTTP GET

# 2. Call: Cached
applicants = api.list_pending_applicants()  # → Cache
```

**Cache-Lebensdauer:** Pro Script-Ausführung

---

## Error Handling

### API nicht erreichbar
```
❌ Fehler beim Laden der API-Daten: ConnectionError...
```
**Lösung:** Prüfe API_URL und Netzwerk

### Bewerber nicht gefunden
```
❌ Bewerber '+49 1234...' nicht in API gefunden
```
**Lösung:** Prüfe ob Bewerber Status "Neu intern" hat

### Campaign nicht gefunden
```
❌ Campaign 16 nicht gefunden. Verfügbare Campaigns: 2
```
**Lösung:** 
- Prüfe ob campaigns eine `id`-Property haben
- Falls nicht: API-Antwort anpassen

### Company nicht gefunden
```
❌ Company 2 nicht gefunden
```
**Lösung:** Prüfe company_id in Campaign

---

## Troubleshooting

### Problem: "USE_API_SOURCE muss auf 'true' gesetzt sein"
**Ursache:** API-Source nicht aktiviert  
**Lösung:** Setze in `.env`: `USE_API_SOURCE=true`

### Problem: "API_URL nicht gesetzt"
**Ursache:** Keine API URL konfiguriert  
**Lösung:** Setze in `.env`: `API_URL=https://...`

### Problem: "Keine Bewerber gefunden"
**Ursache:** API gibt leere Liste zurück  
**Lösung:** 
- Prüfe ob Bewerber Status "Neu intern" haben
- Teste API-Endpoint direkt im Browser/Postman

### Problem: "Zu viele Test-Bewerber"
**Ursache:** Test-Filter deaktiviert  
**Lösung:** Setze in `.env`: `FILTER_TEST_APPLICANTS=true`

### Problem: "Echte Bewerber werden gefiltert"
**Ursache:** Bewerber hat "Test" im Namen (z.B. "Tester" als Nachname)  
**Lösung:** 
- Temporär Filter deaktivieren: `FILTER_TEST_APPLICANTS=false`
- Oder manuell einzeln verarbeiten mit `main.py`

### Problem: "Campaign ID fehlt in API-Antwort"
**Ursache:** campaigns-Array hat keine `id`-Property  
**Lösung:** API-Antwort erweitern um `"id": 16` in jedem campaign-Objekt

---

## Technische Details

### APIDataSource Klasse

**Datei:** `backend/src/data_sources/api_loader.py`

**Methoden:**
- `get_applicant_profile(applicant_id)` - Holt Bewerber-Daten
- `get_applicant_address(applicant_id)` - Gibt leere Adresse zurück (wird im Gespräch erfasst)
- `get_company_profile(campaign_id)` - Holt und transformiert Unternehmensdaten
- `get_conversation_protocol(campaign_id)` - Holt Gesprächsprotokoll
- `list_pending_applicants()` - Gibt alle Bewerber zurück

**Caching:**
```python
self._api_data = None  # Cache

def _load_api_data(self):
    if self._api_data is None:
        self._api_data = requests.get(...).json()
    return self._api_data
```

### Konditionale Adress-Abfrage

**Knowledge Base Builder** prüft ob Adresse vorhanden:

```python
# Datei: backend/src/aggregator/knowledge_base_builder.py

has_address = bool(data.get('street', '').strip())

if has_address:
    # Bestätigungsfrage
    kb += "Ich habe Ihre Adresse als ... notiert. Korrekt?"
else:
    # Erfassungsfrage
    kb += "Nennen Sie mir bitte Ihre vollständige Adresse."
```

**Phase 1 Prompt** enthält beide Varianten:

```markdown
FALLS ADRESSE IN DATEN VORHANDEN:
„Ich habe Ihre Adresse als {{street}} {{house_number}}... Ist das korrekt?"

FALLS ADRESSE NICHT VORHANDEN:
„Nennen Sie mir bitte Ihre vollständige Adresse."
```

---

## Nächste Schritte

### Für Produktion:
1. ✅ API-Credentials in .env setzen
2. ✅ `USE_API_SOURCE=true` aktivieren
3. ✅ `test_api_source.py` ausführen
4. ✅ Batch-Processing testen
5. ⏳ Auf Server deployen (siehe DEPLOYMENT.md)

### Für Entwicklung:
1. ✅ Mit File-Source weiter testen: `USE_API_SOURCE=false`
2. ✅ Mock-Daten verwenden: `backend/test_data/mock_api_response.json`

---

## Weiterführende Dokumentation

- **Deployment:** Siehe `DEPLOYMENT.md`
- **Architektur:** Siehe `MODULAR_TRANSPORT_ARCHITECTURE.md`
- **Testing:** Siehe `test_api_source.py` und `test_dry_run.py`

---

**Erstellt:** November 2025  
**Status:** Produktionsbereit  
**Version:** 1.0

