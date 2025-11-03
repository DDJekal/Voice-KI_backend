# FastAPI Webhook Server - Implementation Complete ✅

**Datum:** November 3, 2025  
**Status:** Bereit für Render.com Deployment

---

## Was wurde implementiert

### Neue Dateien:

1. ✅ **`backend/api_server.py`** (237 Zeilen)
   - FastAPI Server mit Webhook-Endpoint
   - Health Check für Render
   - Async Wrapper für Campaign Setup
   - HOC Upload Integration
   - Logging Middleware
   - Error Handling

2. ✅ **`backend/render.yaml`** 
   - Deployment-Konfiguration für Render.com
   - Environment Variables
   - Build & Start Commands
   - Health Check Path

3. ✅ **`backend/test_webhook.py`**
   - Lokales Test-Script
   - Health Check Test
   - Campaign Setup Test
   - CLI mit Argumenten

4. ✅ **`backend/docs/WEBHOOK_API.md`**
   - Vollständige API-Dokumentation
   - Testing-Guide
   - HOC-Integration Beispiele
   - Troubleshooting

### Erweiterte Dateien:

5. ✅ **`backend/src/storage/campaign_storage.py`**
   - Neue Methode: `upload_to_hoc()`
   - HTTP POST zu HOC Cloud
   - Error Handling & Timeouts

6. ✅ **`backend/src/config.py`**
   - Neue Settings: `webhook_secret`
   - Neue Settings: `hoc_api_url`
   - Neue Settings: `hoc_upload_enabled`

7. ✅ **`backend/requirements.txt`**
   - FastAPI 0.104.1
   - Uvicorn[standard] 0.24.0
   - Python-multipart 0.0.6

8. ✅ **`backend/.gitignore`**
   - Campaign Packages ignoriert
   - Output_ordner ignoriert
   - Test Data ignoriert

---

## Architektur

```
┌─────────────────────────────────────────┐
│         HOC Frontend (Button)           │
│   "Campaign Package erstellen"         │
└───────────────┬─────────────────────────┘
                │
                │ POST /webhook/setup-campaign
                │ Authorization: Bearer <secret>
                ↓
┌─────────────────────────────────────────┐
│    FastAPI Server (Render.com)          │
│                                         │
│  1. Auth prüfen                         │
│  2. Campaign Setup ausführen            │
│  3. Package lokal speichern             │
│  4. Package zu HOC uploaden             │
│  5. Response mit Download-URL           │
└───────────────┬─────────────────────────┘
                │
                │ POST /campaigns/{id}/package
                ↓
┌─────────────────────────────────────────┐
│        HOC Cloud API                    │
│   Speichert Campaign Package            │
└─────────────────────────────────────────┘
```

---

## Endpoints

### 1. Health Check
```
GET /health
→ {"status": "healthy", "version": "1.0.0"}
```

### 2. Setup Campaign Webhook
```
POST /webhook/setup-campaign
Headers: Authorization: Bearer <SECRET>
Body: {"campaign_id": "16", "force_rebuild": false}

→ {
    "status": "success",
    "package_id": "16",
    "download_url": "...",
    "question_count": 15,
    "company_name": "..."
  }
```

---

## Lokales Testing

### 1. Server starten
```bash
cd backend
uvicorn api_server:app --reload --port 8000
```

### 2. Health Check testen
```bash
curl http://localhost:8000/health
```

### 3. Webhook testen
```bash
python test_webhook.py --campaign-id 16
```

**Output:**
```
TEST: Webhook Setup Campaign
======================================================================
URL: http://localhost:8000/webhook/setup-campaign
...
✅ SUCCESS!
📦 Package Info:
   Package ID: 16
   Company: Robert Bosch Krankenhaus
   Questions: 15
   Download URL: local://campaign_packages/16.json
```

---

## Render.com Deployment

### Schritt 1: Code pushen
```bash
git add .
git commit -m "Add FastAPI webhook server for Render deployment"
git push origin main
```

### Schritt 2: Render Service erstellen
1. Gehe zu [render.com](https://render.com/)
2. "New Web Service"
3. GitHub Repo verbinden
4. `render.yaml` wird automatisch erkannt
5. "Create Web Service"

### Schritt 3: Environment Variables setzen
Im Render Dashboard → Service → Environment:

**Required Secrets (manuell setzen):**
- `API_KEY` - Dein HOC API Key
- `ELEVENLABS_API_KEY` - (für später)

**Auto-generiert:**
- `WEBHOOK_SECRET` - Von Render generiert

### Schritt 4: Deploy abwarten
- Build dauert ~2-5 Minuten
- Health Check wird automatisch geprüft
- Status: "Live" ✅

**URL:** `https://voiceki-backend.onrender.com`

### Schritt 5: Production testen
```bash
curl https://voiceki-backend.onrender.com/health
```

```bash
curl -X POST https://voiceki-backend.onrender.com/webhook/setup-campaign \
  -H "Authorization: Bearer <WEBHOOK_SECRET_AUS_RENDER>" \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": "16"}'
```

---

## Environment Variables (Render)

### Automatisch gesetzt (via render.yaml):
- `USE_API_SOURCE=true`
- `API_URL=https://high-office.hirings.cloud/api/v1`
- `API_STATUS=new`
- `FILTER_TEST_APPLICANTS=true`
- `HOC_API_URL=https://high-office.hirings.cloud/api/v1`
- `HOC_UPLOAD_ENABLED=true`

### Manuell setzen (Secrets):
- `API_KEY` - HOC API Key
- `WEBHOOK_SECRET` - Auto-generiert (kopieren für HOC)
- `ELEVENLABS_API_KEY` - Für Phase 2

---

## HOC Integration

### Was HOC noch braucht:

#### 1. Backend Endpoint (HOC-Team)
```
POST /api/v1/campaigns/{id}/package
Authorization: Bearer <API_KEY>
Content-Type: application/json

Body: <Campaign Package JSON>
```

#### 2. Frontend Button (HOC-Team)
```typescript
async function setupCampaign(campaignId) {
  const response = await fetch(
    'https://voiceki-backend.onrender.com/webhook/setup-campaign',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${WEBHOOK_SECRET}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ campaign_id: campaignId })
    }
  );
  
  return await response.json();
}
```

#### 3. Webhook Secret speichern (HOC-Team)
- Kopiere `WEBHOOK_SECRET` aus Render Dashboard
- Speichere in HOC Environment Variables
- Nutze beim Webhook-Call

---

## Features

✅ **FastAPI Webhook Server** - Production-ready  
✅ **Health Check** - Für Render Monitoring  
✅ **Bearer Token Auth** - Sicher & einfach  
✅ **Async Processing** - Non-blocking Setup  
✅ **HOC Upload** - Automatischer Package-Upload  
✅ **Error Handling** - Detaillierte Error-Messages  
✅ **Logging** - Alle Requests geloggt  
✅ **CORS Support** - Für HOC Frontend  
✅ **Request/Response Models** - Pydantic Validation  
✅ **Test-Script** - Lokale Tests einfach  
✅ **Deployment Config** - Render.yaml ready  
✅ **Dokumentation** - Vollständig  

---

## Pre-Deployment Cleanup (Optional)

### Empfohlene Schritte vor erstem Deploy:

```bash
cd backend

# 1. venv aus Git entfernen (falls vorhanden)
git rm -r --cached venv/ 2>/dev/null || true

# 2. __pycache__ entfernen
find . -type d -name "__pycache__" -exec git rm -r --cached {} + 2>/dev/null || true

# 3. Output_ordner entfernen
git rm -r --cached Output_ordner/ 2>/dev/null || true

# 4. Commit
git add .gitignore
git commit -m "Cleanup for Render deployment"
git push
```

**.gitignore ist bereits erweitert** ✅

---

## Monitoring

### Render Dashboard

**Logs ansehen:**
- Render Dashboard → Service → Logs
- Zeigt alle Requests, Errors, Setup-Fortschritt

**Metrics:**
- CPU/Memory Usage
- Request Count
- Response Time

### Health Check

Render prüft automatisch `/health` alle 30 Sekunden.

---

## Troubleshooting

### "Server nicht erreichbar"
**Problem:** Free Tier schläft nach 15min  
**Lösung:** Warte 10-15s (Cold Start) oder upgrade zu Starter ($7/mo)

### "401 Unauthorized"
**Problem:** Falsches/fehlendes Token  
**Lösung:** Prüfe WEBHOOK_SECRET in Render Dashboard

### "questions.json nicht gefunden"
**Problem:** Pfad auf Render anders  
**Lösung:** 
- Prüfe Logs für genauen Fehler
- Evtl. questions.json ins Repo committen
- Oder Pfad in Environment Variables anpassen

### "Build failed"
**Problem:** Dependency-Error  
**Lösung:** Prüfe requirements.txt Syntax

---

## Nächste Schritte

### Sofort:
1. ✅ Code ist bereit
2. ✅ Dokumentation vollständig
3. → **Jetzt**: Deploy auf Render!

### Nach Deployment:
1. Health Check testen
2. Webhook mit echtem Campaign testen
3. WEBHOOK_SECRET an HOC-Team weitergeben
4. HOC-Integration durchführen
5. End-to-End Test mit HOC

### Optional:
1. Custom Domain einrichten
2. Upgrade auf Starter Plan ($7/mo) für 24/7
3. Slack Notifications einrichten
4. Backup-Strategie für Packages

---

## Kosten

**Render Free Tier:**
- ✅ 750 Stunden/Monat kostenlos
- ⚠️ Auto-Sleep nach 15min Inaktivität
- ✅ Ausreichend für Testing

**Render Starter ($7/Monat):**
- ✅ Kein Auto-Sleep
- ✅ 24/7 verfügbar
- ✅ 512MB RAM
- ✅ Empfohlen für Production

---

## Ordnerstruktur

```
backend/
├── api_server.py                    ✨ NEU (Entry Point)
├── test_webhook.py                  ✨ NEU
├── render.yaml                      ✨ NEU
├── requirements.txt                 📝 ERWEITERT
├── .gitignore                       📝 ERWEITERT
├── docs/
│   ├── CAMPAIGN_SETUP.md
│   └── WEBHOOK_API.md               ✨ NEU
├── src/
│   ├── config.py                    📝 ERWEITERT
│   ├── storage/
│   │   └── campaign_storage.py     📝 ERWEITERT
│   ├── campaign/
│   ├── data_sources/
│   └── ...
└── campaign_packages/               (lokal, nicht in Git)
```

---

## Testing Checklist

- [x] Health Check lokal funktioniert
- [x] Webhook lokal funktioniert
- [x] Package wird erstellt
- [x] Package wird gespeichert
- [x] Keine Linter-Errors
- [ ] Deploy auf Render
- [ ] Health Check Production
- [ ] Webhook Production
- [ ] HOC Integration
- [ ] End-to-End Test

---

## Zusammenfassung

Das System ist **vollständig implementiert** und **bereit für Deployment auf Render.com**!

**Was funktioniert:**
- ✅ FastAPI Webhook-Server
- ✅ Campaign Setup via Webhook
- ✅ HOC Upload (wenn Endpoint bereit)
- ✅ Authentifizierung
- ✅ Error Handling
- ✅ Logging
- ✅ Testing

**Was noch fehlt:**
- HOC Backend Endpoint: `POST /campaigns/{id}/package`
- HOC Frontend Button-Integration
- Production Deployment

**Nächster Schritt:**  
→ Deploy auf Render.com! 🚀

---

**Version:** 1.0.0  
**Status:** Production Ready ✅  
**Platform:** Render.com  
**Implementiert:** November 3, 2025

