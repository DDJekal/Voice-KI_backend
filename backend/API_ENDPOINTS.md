# API-Konfiguration - Quick Reference

## Production API Endpoint

**Base URL:** `https://high-office.hirings.cloud/api/v1`

### Endpoints

#### 1. Neue Bewerber
```
GET https://high-office.hirings.cloud/api/v1/applicants/new
```
**Beschreibung:** Bewerber mit Status "Neu intern"

#### 2. Nicht erreichte Bewerber
```
GET https://high-office.hirings.cloud/api/v1/applicants/not_reached
```
**Beschreibung:** Bewerber, die beim ersten Versuch nicht erreicht wurden

---

## Test-Bewerber

**⚠️ WICHTIG:** Die API enthält Test-Bewerber vom Delivering-Team für Zapier-Tests.

**Erkennungsmerkmal:** Diese haben **"Test"** im Vor- oder Nachnamen.

**Automatische Filterung:** Das System filtert diese standardmäßig heraus!

### Beispiele für Test-Bewerber:
- `Max Test`
- `Test Schmidt`
- `Jessica Testmann`

---

## Konfiguration

### In .env setzen:

```env
# API aktivieren
USE_API_SOURCE=true

# API URL (Production)
API_URL=https://high-office.hirings.cloud/api/v1

# API Key (falls benötigt)
API_KEY=your_key_here

# Status: "new" oder "not_reached"
API_STATUS=new

# Test-Filter (empfohlen: true)
FILTER_TEST_APPLICANTS=true
```

---

## Status wechseln

### Neue Bewerber verarbeiten (default):
```env
API_STATUS=new
```

### Nicht erreichte Bewerber verarbeiten:
```env
API_STATUS=not_reached
```

### Test-Filter deaktivieren (nicht empfohlen):
```env
FILTER_TEST_APPLICANTS=false
```

---

## Verwendung

### Alle neuen Bewerber verarbeiten:
```bash
cd backend

# In .env: API_STATUS=new
python process_all_applicants.py
```

### Alle nicht erreichten Bewerber verarbeiten:
```bash
cd backend

# In .env: API_STATUS=not_reached
python process_all_applicants.py
```

### Test-Run mit Test-Bewerbern:
```bash
# In .env:
# FILTER_TEST_APPLICANTS=false
python test_api_source.py
```

---

## Filter-Logik

Das System filtert automatisch Bewerber, die **"test"** (case-insensitive) im Namen haben:

```python
def _is_test_applicant(applicant):
    first_name = applicant['first_name'].lower()
    last_name = applicant['last_name'].lower()
    
    return 'test' in first_name or 'test' in last_name
```

**Output beim Filtern:**
```
📡 Lade Daten von: https://high-office.hirings.cloud/api/v1/applicants/new
⚠️  3 Test-Bewerber herausgefiltert
✅ API-Daten geladen: 12 Bewerber (Status: new)
```

---

## Troubleshooting

### Problem: "Zu viele Test-Bewerber werden verarbeitet"
**Lösung:** Prüfe ob `FILTER_TEST_APPLICANTS=true` in .env

### Problem: "Echte Bewerber werden gefiltert"
**Ursache:** Bewerber hat "Test" im Namen (z.B. "Tester" als Nachname)  
**Lösung:** Filter deaktivieren oder Filterlogik anpassen

### Problem: "API gibt leere Liste zurück"
**Ursache:** Kein Bewerber mit diesem Status vorhanden  
**Lösung:** Prüfe im Backend/Dashboard ob Bewerber existieren

---

**Erstellt:** November 3, 2025  
**Status:** Production Ready  
**API:** hirings.cloud

