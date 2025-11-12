# 🔗 VoiceKI Tool - Integration Guide für HOC

**Version:** 2.0.0 (Direkte Daten-Übertragung)  
**Stand:** 12. November 2025

---

## 🎯 **Quick Start**

### **Was HOC braucht:**

1. ✅ **API-URL:** `https://voice-ki-backend.onrender.com`
2. ✅ **WEBHOOK_SECRET:** Von David erhalten
3. ✅ **Company-Daten** bereitstellen
4. ✅ **Conversation Protocol** (Gesprächsprotokoll) bereitstellen

---

## 📥 **API-Request Format**

### **Endpoint:**
```
POST https://voice-ki-backend.onrender.com/webhook/setup-campaign
```

### **Headers:**
```http
Authorization: Bearer <WEBHOOK_SECRET>
Content-Type: application/json
```

### **Request Body:**

```json
{
  "campaign_id": "62",
  "company": {
    "name": "Urban Consult GmbH",
    "size": "50",
    "address": "Hauptstraße 123, 10115 Berlin",
    "benefits": "30 Tage Urlaub, attraktive Vergütung...",
    "target_group": "Sozialpädagogen",
    "website": "https://urban-consult.de",
    "career_page": "https://urban-consult.de/karriere",
    "privacy_url": "https://urban-consult.de/datenschutz",
    "impressum": "https://urban-consult.de/impressum"
  },
  "conversation_protocol": {
    "id": 62,
    "name": "Leitungskraft für unsere Kita (mwd)",
    "pages": [
      {
        "id": 87,
        "name": "Der Bewerber erfüllt folgende Kriterien:",
        "position": 1,
        "prompts": [
          {
            "id": 291,
            "question": "Zwingend: staatlich anerkannter Abschluss in einem sozialpädagogischen Beruf",
            "position": 1
          },
          {
            "id": 289,
            "question": "Zwingend: Deutschkenntnisse B2",
            "position": 2
          }
        ]
      },
      {
        "id": 88,
        "name": "Der Bewerber akzeptiert folgende Rahmenbedingungen:",
        "position": 2,
        "prompts": [
          {
            "id": 297,
            "question": "30 Tage Jahresurlaub",
            "position": 1
          },
          {
            "id": 295,
            "question": "Vollzeit (39 Wochenstunden)",
            "position": 2
          }
        ]
      }
    ]
  },
  "force_rebuild": false
}
```

---

## 💻 **TypeScript Integration**

```typescript
// types.ts
interface CompanyData {
  name: string;
  size?: string;
  address?: string;
  benefits?: string;
  target_group?: string;
  website?: string;
  career_page?: string;
  privacy_url?: string;
  impressum?: string;
}

interface PromptData {
  id: number;
  question: string;
  position: number;
}

interface PageData {
  id: number;
  name: string;
  position: number;
  prompts: PromptData[];
}

interface ConversationProtocol {
  id: number;
  name: string;
  pages: PageData[];
}

interface VoiceKIRequest {
  campaign_id: string;
  company: CompanyData;
  conversation_protocol: ConversationProtocol;
  force_rebuild?: boolean;
}

interface VoiceKIResponse {
  status: string;
  package_id: string;
  created_at: string;
  question_count: number;
  company_name: string;
  download_url: string;
}

// api.ts
const VOICEKI_API_URL = 'https://voice-ki-backend.onrender.com';
const VOICEKI_WEBHOOK_SECRET = process.env.VOICEKI_WEBHOOK_SECRET;

export async function setupCampaignVoiceKI(
  campaign: Campaign
): Promise<VoiceKIResponse> {
  const response = await fetch(
    `${VOICEKI_API_URL}/webhook/setup-campaign`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${VOICEKI_WEBHOOK_SECRET}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        campaign_id: campaign.id.toString(),
        company: {
          name: campaign.company.name,
          size: campaign.company.size || '',
          address: campaign.company.address || '',
          benefits: campaign.company.benefits || '',
          target_group: campaign.company.target_group || '',
          website: campaign.company.website || '',
          career_page: campaign.company.career_page || '',
          privacy_url: campaign.company.privacy_url || '',
          impressum: campaign.company.impressum || ''
        },
        conversation_protocol: {
          id: campaign.transcript.id,
          name: campaign.transcript.name || campaign.name,
          pages: campaign.transcript.pages
        },
        force_rebuild: false
      } as VoiceKIRequest)
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`VoiceKI Setup failed: ${error.detail || response.statusText}`);
  }

  return await response.json();
}
```

---

## 🎨 **React Component Beispiel**

```tsx
// components/VoiceKISetupButton.tsx
import { useState } from 'react';
import { setupCampaignVoiceKI } from '@/api/voiceki';

export function VoiceKISetupButton({ campaign }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleSetup() {
    setLoading(true);
    setError(null);

    try {
      const response = await setupCampaignVoiceKI(campaign);
      setResult(response);
      
      // Erfolgs-Notification
      toast.success(
        `✅ VoiceKI Package erstellt!\n${response.question_count} Fragen generiert`
      );
      
    } catch (err) {
      setError(err.message);
      toast.error('❌ VoiceKI Setup fehlgeschlagen');
    } finally {
      setLoading(false);
    }
  }

  if (result) {
    return (
      <div className="voiceki-success">
        <div className="flex items-center gap-2">
          <span className="text-green-600">✅ VoiceKI konfiguriert</span>
        </div>
        <p className="text-sm text-gray-600">
          {result.question_count} Fragen generiert
        </p>
        <button 
          onClick={handleSetup}
          className="btn-secondary"
        >
          🔄 Package neu generieren
        </button>
      </div>
    );
  }

  return (
    <div className="voiceki-setup">
      <button 
        onClick={handleSetup} 
        disabled={loading}
        className="btn-primary"
      >
        {loading ? (
          <>
            <Spinner />
            Erstelle Package...
          </>
        ) : (
          <>
            🎙️ VoiceKI Package erstellen
          </>
        )}
      </button>
      
      {error && (
        <p className="text-red-600 text-sm mt-2">
          Fehler: {error}
        </p>
      )}
    </div>
  );
}
```

---

## 📤 **Response Format**

```json
{
  "status": "success",
  "package_id": "62",
  "created_at": "2025-11-12T10:30:00Z",
  "question_count": 8,
  "company_name": "Urban Consult GmbH",
  "download_url": "https://voice-ki-backend.onrender.com/campaigns/62/package"
}
```

---

## ✅ **Was das Tool macht**

1. ✅ Empfängt Company-Daten und Conversation Protocol von HOC
2. ✅ Generiert automatisch Questions mit OpenAI (basierend auf Protocol)
3. ✅ Erstellt Campaign Package (verschlankte Struktur)
4. ✅ Speichert Package (abrufbar über GET-Endpoint)
5. ✅ Gibt Response mit Package-Info zurück

---

## 🔑 **Authentifizierung**

**WEBHOOK_SECRET:**
- Wird von Render.com generiert
- Muss von David bereitgestellt werden
- Im HOC Environment als Variable speichern:

```env
# HOC .env.production
VOICEKI_WEBHOOK_SECRET=<von_david_erhalten>
```

---

## 🧪 **Testing**

### **cURL Beispiel:**

```bash
curl -X POST https://voice-ki-backend.onrender.com/webhook/setup-campaign \
  -H "Authorization: Bearer <WEBHOOK_SECRET>" \
  -H "Content-Type: application/json" \
  -d @payload.json
```

**payload.json:**
```json
{
  "campaign_id": "62",
  "company": {
    "name": "Test Company"
  },
  "conversation_protocol": {
    "id": 62,
    "name": "Test Campaign",
    "pages": [
      {
        "id": 1,
        "name": "Qualifikationen",
        "position": 1,
        "prompts": [
          {
            "id": 1,
            "question": "Haben Sie einen Abschluss?",
            "position": 1
          }
        ]
      }
    ]
  }
}
```

---

## ⚠️ **Error Handling**

### **401 Unauthorized**
```json
{
  "detail": "Invalid authorization token"
}
```
→ WEBHOOK_SECRET prüfen

### **400 Bad Request**
```json
{
  "detail": "Validation error: ..."
}
```
→ Request-Format prüfen (alle Pflichtfelder vorhanden?)

### **500 Internal Server Error**
```json
{
  "detail": "Internal server error: ..."
}
```
→ Logs auf Render.com prüfen oder David kontaktieren

---

## 📊 **Vorteile des neuen Ansatzes**

| Aspekt | Vorteil |
|--------|---------|
| **Geschwindigkeit** | ✅ Schneller (1 statt 2 API-Calls) |
| **Unabhängigkeit** | ✅ Keine Abhängigkeit von HOC API |
| **Kontrolle** | ✅ HOC entscheidet, welche Daten gesendet werden |
| **Fehlerquellen** | ✅ Weniger Fehleranfällig |
| **Testing** | ✅ Einfacher zu testen |

---

## 📋 **Checklist für HOC**

- [ ] WEBHOOK_SECRET von David erhalten
- [ ] Environment Variable `VOICEKI_WEBHOOK_SECRET` setzen
- [ ] API-Call Funktion implementieren
- [ ] Button in Campaign-Detail einbauen
- [ ] TypeScript Types erstellen
- [ ] Error-Handling implementieren
- [ ] Success-Notification einbauen
- [ ] Testing durchführen
- [ ] Production Deployment

---

## 🆘 **Support**

Bei Fragen oder Problemen:
- **Kontakt:** David (VoiceKI Tool Betreiber)
- **Logs:** Render.com Dashboard
- **Dokumentation:** Siehe `API_DOCUMENTATION.md`

---

**Version:** 2.0.0  
**Änderung:** Tool empfängt Daten direkt von HOC (kein API-Polling mehr)  
**Datum:** 12. November 2025

