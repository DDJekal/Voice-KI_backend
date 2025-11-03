# Webhook API Documentation

**Version:** 1.0.0  
**Base URL:** `https://voiceki-backend.onrender.com`  
**Local Dev:** `http://localhost:8000`

---

## Endpoints

### 1. Health Check

**GET** `/health`

Prüft ob Server läuft (wird von Render.com für Health Checks genutzt).

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-03T12:00:00"
}
```

---

### 2. Setup Campaign Webhook

**POST** `/webhook/setup-campaign`

Erstellt Campaign Package und uploaded zu HOC Cloud.

**Headers:**
```
Authorization: Bearer <WEBHOOK_SECRET>
Content-Type: application/json
```

**Request Body:**
```json
{
  "campaign_id": "16",
  "force_rebuild": false
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "package_id": "16",
  "created_at": "2025-11-03T12:30:00Z",
  "download_url": "https://hoc.cloud/api/v1/campaigns/16/package",
  "question_count": 15,
  "company_name": "Robert Bosch Krankenhaus"
}
```

**Error Responses:**

- **401 Unauthorized** - Falsches/fehlendes Token
```json
{
  "detail": "Invalid authorization token"
}
```

- **404 Not Found** - Campaign oder questions.json nicht gefunden
```json
{
  "detail": "questions.json nicht gefunden: ..."
}
```

- **400 Bad Request** - Validation Error
```json
{
  "detail": "Invalid campaign_id format"
}
```

- **500 Internal Server Error** - Setup fehlgeschlagen
```json
{
  "detail": "Internal server error: ..."
}
```

---

## Authentication

Webhook nutzt Bearer Token Authentication.

**Header:**
```
Authorization: Bearer <WEBHOOK_SECRET>
```

**WEBHOOK_SECRET:**
- Wird von Render.com auto-generiert
- Findest du in Render Dashboard → Service → Environment
- Muss in HOC-Frontend konfiguriert werden

---

## Testing

### Lokal testen

**1. Server starten:**
```bash
cd backend
uvicorn api_server:app --reload --port 8000
```

**2. Health Check:**
```bash
curl http://localhost:8000/health
```

**3. Webhook testen:**
```bash
python test_webhook.py --campaign-id 16
```

Oder mit curl:
```bash
curl -X POST http://localhost:8000/webhook/setup-campaign \
  -H "Authorization: Bearer test_secret" \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": "16"}'
```

### Production testen

```bash
curl -X POST https://voiceki-backend.onrender.com/webhook/setup-campaign \
  -H "Authorization: Bearer <DEIN_WEBHOOK_SECRET>" \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": "16"}'
```

**Webhook Secret aus Render Dashboard kopieren!**

---

## HOC Integration

### Frontend (TypeScript/React)

```typescript
async function setupCampaign(campaignId: string) {
  const response = await fetch(
    'https://voiceki-backend.onrender.com/webhook/setup-campaign',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${WEBHOOK_SECRET}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        campaign_id: campaignId,
        force_rebuild: false
      })
    }
  );
  
  if (!response.ok) {
    throw new Error(`Setup failed: ${response.statusText}`);
  }
  
  const result = await response.json();
  console.log('Package created:', result);
  
  return result;
}
```

### Backend (Package speichern)

HOC muss diesen Endpoint bereitstellen:

```
POST /api/v1/campaigns/{id}/package
Authorization: Bearer <HOC_API_KEY>
Content-Type: application/json

Body: <Campaign Package JSON>
```

---

## Monitoring

### Logs (Render Dashboard)

- Render Dashboard → Service → Logs
- Zeigt alle Requests, Errors, Setup-Fortschritt

**Beispiel-Log:**
```
INFO - Request: POST /webhook/setup-campaign
INFO - Setup triggered for campaign 16
INFO - 🔧 Erstelle Campaign Package für Campaign 16
INFO - 1️⃣ Lade questions.json...
INFO - ✅ 15 Fragen geladen
...
INFO - Response: 200 (5.23s)
```

### Metrics (Render Dashboard)

- CPU Usage
- Memory Usage
- Request Count
- Response Time

---

## Troubleshooting

### "Server nicht erreichbar"
**Ursache:** Server schläft (Free Tier) oder offline  
**Lösung:** Warte 10-15s (Cold Start) oder upgraden auf Starter Plan

### "401 Unauthorized"
**Ursache:** Falsches/fehlendes Token  
**Lösung:** Prüfe WEBHOOK_SECRET in Render Dashboard

### "questions.json nicht gefunden"
**Ursache:** TypeScript Tool nicht ausgeführt  
**Lösung:** In Render: Paths prüfen oder questions.json ins Repo

### "Timeout (>60s)"
**Ursache:** Setup dauert zu lange  
**Lösung:** 
- Prüfe Logs für Fehler
- Evtl. force_rebuild=false nutzen (cached Package)

---

## Deployment Checklist

- [ ] Code auf GitHub gepusht
- [ ] Render Service erstellt
- [ ] Environment Variables gesetzt (API_KEY, etc.)
- [ ] Health Check funktioniert (`/health`)
- [ ] Webhook getestet (mit test_webhook.py)
- [ ] WEBHOOK_SECRET an HOC-Team weitergegeben
- [ ] HOC-Frontend integriert
- [ ] Production Test durchgeführt

---

## Rate Limits

**Render Free Tier:**
- Kein explizites Rate Limit
- Auto-Sleep nach 15min Inaktivität

**Empfehlung:**
- Max 1 Request pro Sekunde
- Bei Batch-Processing: Delay zwischen Requests

---

## Security

- ✅ HTTPS via Render (automatisch)
- ✅ Bearer Token Authentication
- ✅ API Keys als Environment Variables
- ✅ CORS nur für notwendige Origins
- ✅ Input Validation mit Pydantic
- ✅ Error Messages ohne sensitive Daten

---

**Support:** Bei Problemen Logs aus Render Dashboard teilen  
**Docs:** Siehe auch `CAMPAIGN_SETUP.md` für Setup-Details

