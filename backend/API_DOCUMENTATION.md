# VoiceKI API Dokumentation

**Version:** 1.0.0  
**Base URL (Production):** `https://voiceki-backend.onrender.com`  
**Base URL (Local):** `http://localhost:8000`

---

## Authentifizierung

Alle Endpoints (außer `/health`) benötigen Bearer Token Authentifizierung:

```
Authorization: Bearer <WEBHOOK_SECRET>
```

Das `WEBHOOK_SECRET` wird von Render.com generiert und ist im Dashboard zu finden.

---

## Endpoints

### 1. Health Check

**GET** `/health`

Prüft ob der Server läuft.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-12T10:00:00"
}
```

**Keine Authentifizierung benötigt.**

---

### 2. Campaign Setup (Webhook)

**POST** `/webhook/setup-campaign`

Erstellt automatisch ein Campaign Package mit OpenAI-generierten Questions.

**Headers:**
```
Authorization: Bearer <WEBHOOK_SECRET>
Content-Type: application/json
```

**Request Body:**
```json
{
  "campaign_id": "1167",
  "force_rebuild": false
}
```

**Parameter:**
- `campaign_id` (string, required): Die Campaign ID
- `force_rebuild` (boolean, optional): Überschreibt existierendes Package. Default: `false`

**Response (200 OK):**
```json
{
  "status": "success",
  "package_id": "1167",
  "created_at": "2025-11-12T09:36:09Z",
  "download_url": "https://high-office.hirings.cloud/api/v1/campaigns/1167/package",
  "question_count": 6,
  "company_name": "Reisecenter alltours GmbH"
}
```

**Was passiert:**
1. Campaign-Daten werden von HOC API geladen
2. Questions werden automatisch mit OpenAI generiert
3. Campaign Package wird erstellt (verschlankte Struktur)
4. Package wird lokal gespeichert
5. Package wird zur HOC API hochgeladen
6. Response mit Package-Info

**Error Responses:**

- **401 Unauthorized** - Falsches/fehlendes Token
- **404 Not Found** - Campaign nicht gefunden
- **500 Internal Server Error** - Setup fehlgeschlagen

---

### 3. Package abrufen

**GET** `/campaigns/{campaign_id}/package`

Gibt ein spezifisches Campaign Package zurück.

**Headers:**
```
Authorization: Bearer <WEBHOOK_SECRET>
```

**URL Parameter:**
- `campaign_id` (string): Die Campaign ID

**Response (200 OK):**
```json
{
  "company_name": "Reisecenter alltours GmbH",
  "campaign_id": "1167",
  "campaign_name": "Tourismusfachkräfte (m/w/d) Berlin",
  "created_at": "2025-11-12T09:36:09Z",
  "company_info": {
    "size": "",
    "address": "Dreischeibenhaus 1, 40211 Düsseldorf",
    "benefits": "",
    "website": "",
    "privacy_url": "",
    "career_page": ""
  },
  "questions": {
    "questions": [
      {
        "id": "gate_abgeschlossene_ausbildung...",
        "question": "Haben Sie: Abgeschlossene Ausbildung...",
        "type": "boolean",
        "preamble": null,
        "options": null,
        "priority": 1,
        "group": "Qualifikation",
        "help_text": null,
        "context": "Muss-Kriterium: ...",
        "category": "standardqualifikationen",
        "category_order": 1
      }
    ]
  }
}
```

**Nutzen:**
- Fallback wenn automatischer Upload fehlschlägt
- Package jederzeit abrufbar
- Für Testing/Debugging

**Error Responses:**

- **401 Unauthorized** - Falsches/fehlendes Token
- **404 Not Found** - Package existiert nicht
- **500 Internal Server Error** - Laden fehlgeschlagen

---

### 4. Campaign Liste

**GET** `/campaigns`

Listet alle verfügbaren Campaign Packages.

**Headers:**
```
Authorization: Bearer <WEBHOOK_SECRET>
```

**Response (200 OK):**
```json
{
  "count": 2,
  "campaigns": [
    {
      "campaign_id": "1167",
      "company_name": "Reisecenter alltours GmbH",
      "campaign_name": "Tourismusfachkräfte (m/w/d) Berlin",
      "created_at": "2025-11-12T09:36:09Z",
      "question_count": 6
    },
    {
      "campaign_id": "65",
      "company_name": "Robert Bosch Krankenhaus Stuttgart",
      "campaign_name": "",
      "created_at": "2025-11-04T09:13:50Z",
      "question_count": 15
    }
  ]
}
```

**Nutzen:**
- Übersicht über alle erstellten Packages
- Monitoring/Debugging

**Error Responses:**

- **401 Unauthorized** - Falsches/fehlendes Token
- **500 Internal Server Error** - Laden fehlgeschlagen

---

## Campaign Package Struktur

### Verschlankte Struktur (NEU!)

Die Packages enthalten nur noch die essentiellen Felder:

**Pro Question:**
- ✅ `id` - Eindeutige ID
- ✅ `question` - Fragentext
- ✅ `type` - Fragetyp (boolean, choice, string, etc.)
- ✅ `preamble` - Einleitung zur Frage (optional)
- ✅ `options` - Antwortoptionen bei choice-Fragen
- ✅ `priority` - Priorität (1=hoch, 2=mittel, 3=niedrig)
- ✅ `group` - Gruppierung (Qualifikation, Rahmen, etc.)
- ✅ `help_text` - Hilfetext (optional)
- ✅ `context` - Kontext-Information (optional)
- ✅ `category` - Kategorie
- ✅ `category_order` - Sortierung

**Entfernte Felder (nicht mehr im Export):**
- ❌ `conversation_flow` - Nur intern verwendet
- ❌ `required` - Nur intern verwendet
- ❌ `input_hint` - Nur intern verwendet
- ❌ `conditions` - Nur intern verwendet
- ❌ `source` - Nur intern verwendet
- ❌ `slot_config` - Nur intern verwendet
- ❌ `gate_config` - Nur intern verwendet
- ❌ `conversation_hints` - Nur intern verwendet

**Keine Meta-Blöcke mehr:**
- ❌ `meta` am Ende des Packages
- ❌ `meta` innerhalb von `questions`

---

## Integration HOC Frontend

### Beispiel: Campaign Setup Button

```typescript
import { useState } from 'react';

function CampaignSetupButton({ campaignId }: { campaignId: string }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  async function setupVoiceKI() {
    setLoading(true);
    
    try {
      const response = await fetch(
        'https://voiceki-backend.onrender.com/webhook/setup-campaign',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${process.env.VOICEKI_WEBHOOK_SECRET}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ 
            campaign_id: campaignId,
            force_rebuild: false 
          })
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      setResult(data);
      
      // Erfolg anzeigen
      alert(`Campaign Package erstellt!\n${data.question_count} Fragen generiert`);
      
    } catch (error) {
      console.error('VoiceKI Setup failed:', error);
      alert('VoiceKI Setup fehlgeschlagen');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button 
        onClick={setupVoiceKI} 
        disabled={loading}
      >
        {loading ? '⏳ Erstelle Package...' : '🎙️ VoiceKI Package erstellen'}
      </button>
      
      {result && (
        <div>
          ✅ Package erstellt: {result.question_count} Fragen
        </div>
      )}
    </div>
  );
}
```

### Beispiel: Package abrufen

```typescript
async function getPackage(campaignId: string) {
  const response = await fetch(
    `https://voiceki-backend.onrender.com/campaigns/${campaignId}/package`,
    {
      headers: {
        'Authorization': `Bearer ${process.env.VOICEKI_WEBHOOK_SECRET}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error(`Package nicht gefunden: ${response.status}`);
  }
  
  return await response.json();
}
```

### Beispiel: Campaign Liste

```typescript
async function listCampaigns() {
  const response = await fetch(
    'https://voiceki-backend.onrender.com/campaigns',
    {
      headers: {
        'Authorization': `Bearer ${process.env.VOICEKI_WEBHOOK_SECRET}`
      }
    }
  );
  
  const data = await response.json();
  console.log(`${data.count} Campaigns verfügbar:`, data.campaigns);
  return data;
}
```

---

## Testing

### 1. Health Check
```bash
curl https://voiceki-backend.onrender.com/health
```

### 2. Campaign Setup
```bash
curl -X POST https://voiceki-backend.onrender.com/webhook/setup-campaign \
  -H "Authorization: Bearer <WEBHOOK_SECRET>" \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": "1167", "force_rebuild": true}'
```

### 3. Package abrufen
```bash
curl https://voiceki-backend.onrender.com/campaigns/1167/package \
  -H "Authorization: Bearer <WEBHOOK_SECRET>"
```

### 4. Campaign Liste
```bash
curl https://voiceki-backend.onrender.com/campaigns \
  -H "Authorization: Bearer <WEBHOOK_SECRET>"
```

---

## Environment Variables

### Auf Render.com (VoiceKI Backend)

```env
OPENAI_API_KEY=sk_...
API_KEY=<HOC_API_KEY>
WEBHOOK_SECRET=<generiert_von_render>
HOC_UPLOAD_ENABLED=true
HOC_API_URL=https://high-office.hirings.cloud/api/v1
API_URL=https://high-office.hirings.cloud/api/v1
```

### Auf HOC-Seite (Frontend)

```env
VOICEKI_WEBHOOK_SECRET=<kopiert_von_render>
VOICEKI_API_URL=https://voiceki-backend.onrender.com
```

---

## Fehlerbehandlung

### Typische Fehler

**401 Unauthorized**
```json
{
  "detail": "Invalid authorization token"
}
```
→ Prüfe WEBHOOK_SECRET

**404 Not Found**
```json
{
  "detail": "Campaign Package 1167 nicht gefunden. Bitte zuerst Setup durchführen."
}
```
→ Package existiert nicht, zuerst Setup aufrufen

**500 Internal Server Error**
```json
{
  "detail": "Internal server error: ..."
}
```
→ Logs auf Render.com prüfen

---

## Monitoring

### Logs ansehen

Render Dashboard → Service → Logs

Zeigt alle Requests, Errors und Setup-Fortschritt.

### Metrics

Render Dashboard → Service → Metrics
- CPU/Memory Usage
- Request Count
- Response Time

---

## Kosten

**Render Free Tier:**
- ✅ 750 Stunden/Monat kostenlos
- ⚠️ Auto-Sleep nach 15min Inaktivität
- ⏱️ Cold Start: 10-15 Sekunden

**Render Starter ($7/Monat):**
- ✅ Kein Auto-Sleep
- ✅ 24/7 verfügbar
- ✅ 512MB RAM
- ✅ Empfohlen für Production

---

## Support

Bei Problemen:
1. Health Check prüfen: `/health`
2. Logs auf Render.com ansehen
3. Environment Variables prüfen
4. API-Dokumentation konsultieren

---

**Version:** 1.0.0  
**Erstellt:** 12. November 2025  
**Status:** Production Ready ✅

