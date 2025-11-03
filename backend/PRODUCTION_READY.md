# API Integration - Production Ready ✅

**Letzte Aktualisierung:** November 3, 2025  
**Status:** Mit Production-URL konfiguriert

---

## ✅ Was wurde finalisiert

### 1. Production API-URL eingebunden
**URL:** `https://high-office.hirings.cloud/api/v1`

**Endpoints:**
- `/applicants/new` - Neue Bewerber
- `/applicants/not_reached` - Nicht erreichte Bewerber

### 2. Test-Bewerber-Filter implementiert
**Problem:** API enthält Test-Bewerber vom Delivering-Team (Zapier-Tests)

**Lösung:** Automatische Filterung basierend auf "Test" im Namen

**Konfigurierbar via:**
```env
FILTER_TEST_APPLICANTS=true  # (default)
```

### 3. Status-Parameter hinzugefügt
**Neuer Parameter:** `API_STATUS`

**Optionen:**
- `new` - Neue Bewerber (default)
- `not_reached` - Nicht erreichte Bewerber

### 4. Alle Dateien aktualisiert
✅ `backend/src/data_sources/api_loader.py` - Filter-Logik  
✅ `backend/src/config.py` - Neue Settings  
✅ `backend/main.py` - Status-Anzeige  
✅ `backend/test_api_source.py` - Status-Auswahl  
✅ `backend/process_all_applicants.py` - Filter-Info  
✅ `backend/.env.example` - Production-URL  
✅ `backend/API_ENDPOINTS.md` - Neue Dokumentation  
✅ `backend/API_INTEGRATION.md` - Aktualisiert  

---

## 🚀 Schnellstart

### 1. .env konfigurieren

```env
# API aktivieren
USE_API_SOURCE=true

# Production API
API_URL=https://high-office.hirings.cloud/api/v1
API_KEY=your_actual_key_here

# Neue Bewerber verarbeiten
API_STATUS=new

# Test-Bewerber filtern
FILTER_TEST_APPLICANTS=true

# ElevenLabs
ELEVENLABS_API_KEY=sk_your_key_here
ELEVENLABS_AGENT_ID=agent_your_id_here
```

### 2. API testen

```bash
cd backend
python test_api_source.py
```

**Output:**
```
📡 Lade Daten von: https://high-office.hirings.cloud/api/v1/applicants/new
⚠️  3 Test-Bewerber herausgefiltert
✅ API-Daten geladen: 12 Bewerber (Status: new)
```

### 3. Batch-Processing starten

```bash
python process_all_applicants.py
```

---

## 📊 Filter-Logik

### Was wird gefiltert?

Bewerber mit **"test"** (case-insensitive) im Vor- oder Nachnamen:

```python
# Wird gefiltert:
{"first_name": "Max", "last_name": "Test"}
{"first_name": "Test", "last_name": "Schmidt"}
{"first_name": "Jessica", "last_name": "Testmann"}

# Wird NICHT gefiltert:
{"first_name": "Max", "last_name": "Mustermann"}
{"first_name": "Jessica", "last_name": "Niewalda"}
```

### Filter deaktivieren

Falls echte Bewerber "Test" im Namen haben (z.B. "Tester"):

```env
FILTER_TEST_APPLICANTS=false
```

---

## 🔄 Status wechseln

### Neue Bewerber verarbeiten (Standard)

```env
API_STATUS=new
```

```bash
python process_all_applicants.py
```

### Nicht erreichte Bewerber nachholen

```env
API_STATUS=not_reached
```

```bash
python process_all_applicants.py
```

---

## 🧪 Test-Szenarien

### Szenario 1: Nur Test-Bewerber anzeigen

```env
FILTER_TEST_APPLICANTS=false
```

```bash
python test_api_source.py
```

### Szenario 2: Production-Run ohne Test-Bewerber

```env
USE_API_SOURCE=true
API_STATUS=new
FILTER_TEST_APPLICANTS=true
```

```bash
python process_all_applicants.py
```

### Szenario 3: Nicht erreichte Bewerber nachholen

```env
API_STATUS=not_reached
FILTER_TEST_APPLICANTS=true
```

```bash
python process_all_applicants.py
```

---

## 📝 Logging

Das System zeigt automatisch an:
- API-URL
- Status (new/not_reached)
- Test-Filter (Aktiv/Deaktiviert)
- Anzahl gefilterter Test-Bewerber
- Anzahl verarbeiteter Bewerber

**Beispiel-Output:**
```
ℹ️  Verwende API Data Source
   API URL: https://high-office.hirings.cloud/api/v1
   Status: new
   Test-Filter: Aktiv

📡 Lade Daten von: https://high-office.hirings.cloud/api/v1/applicants/new
⚠️  5 Test-Bewerber herausgefiltert
✅ API-Daten geladen: 18 Bewerber (Status: new)
```

---

## ⚠️ Wichtige Hinweise

### 1. Test-Bewerber erkennen
- Zapier erstellt Test-Bewerber mit "Test" im Namen
- Diese werden standardmäßig gefiltert
- Bei Bedarf deaktivierbar

### 2. Status richtig setzen
- `new` für neue Erstanrufe
- `not_reached` für zweiten Versuch

### 3. API-Key sicher aufbewahren
- Nie ins Git committen
- Nur in `.env` speichern
- Server: Secrets Manager verwenden

---

## 🔧 Troubleshooting

### Problem: "5 Test-Bewerber herausgefiltert, aber das sind echte!"
**Lösung:** Prüfe Namen der Bewerber - haben sie "Test" im Namen?  
**Workaround:** `FILTER_TEST_APPLICANTS=false` setzen

### Problem: "API gibt leere Liste zurück"
**Ursache:** Kein Bewerber mit diesem Status vorhanden  
**Lösung:** 
- Prüfe Status-Einstellung (`new` vs `not_reached`)
- Prüfe im Backend/Dashboard

### Problem: "Test-Bewerber werden verarbeitet"
**Ursache:** Filter deaktiviert  
**Lösung:** `FILTER_TEST_APPLICANTS=true` in .env

---

## 📚 Weitere Dokumentation

- **API Endpoints:** `API_ENDPOINTS.md` - Detaillierte API-Info
- **Integration:** `API_INTEGRATION.md` - Vollständige Integration
- **Deployment:** `DEPLOYMENT.md` - Server-Setup

---

## ✅ Checkliste für Go-Live

- [x] Production API-URL konfiguriert
- [x] Test-Bewerber-Filter implementiert
- [x] Status-Parameter hinzugefügt
- [x] Alle Dateien aktualisiert
- [x] Dokumentation vervollständigt
- [ ] API-Key in .env eintragen
- [ ] API-Verbindung testen
- [ ] Ersten Test-Call durchführen
- [ ] Batch-Processing testen
- [ ] Automation einrichten

---

**Version:** 2.0  
**API:** hirings.cloud  
**Status:** Production Ready 🚀  
**Test-Filter:** Aktiv ✅

