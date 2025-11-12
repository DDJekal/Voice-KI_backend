# 🎯 VoiceKI Protocol Processor - API v3.0

**Einfacher Microservice: Protocol rein, Questions raus!**

---

## 📋 **Quick Start**

### **Endpoint:**
```
POST https://voice-ki-backend.onrender.com/webhook/process-protocol
```

### **Auth:**
```
Authorization: Bearer <WEBHOOK_SECRET>
```

### **Input:**
```json
{
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
        }
      ]
    }
  ]
}
```

### **Output:**
```json
{
  "protocol_id": 62,
  "protocol_name": "Leitungskraft für unsere Kita (mwd)",
  "processed_at": "2025-11-12T11:00:00Z",
  "question_count": 8,
  "questions": [
    {
      "id": "gate_staatlich_anerkannter_abschluss",
      "question": "Haben Sie einen staatlich anerkannten Abschluss in einem sozialpädagogischen Beruf?",
      "type": "boolean",
      "priority": 1,
      "group": "Qualifikation",
      "context": "Muss-Kriterium",
      "category": "standardqualifikationen",
      "category_order": 1
    }
  ]
}
```

---

## 💻 **TypeScript Integration**

```typescript
// types.ts
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

interface Question {
  id: string;
  question: string;
  type: string;
  preamble?: string | null;
  options?: string[] | null;
  priority: number;
  group?: string | null;
  help_text?: string | null;
  context?: string | null;
  category?: string;
  category_order?: number;
}

interface ProcessProtocolResponse {
  protocol_id: number;
  protocol_name: string;
  processed_at: string;
  question_count: number;
  questions: Question[];
}

// api.ts
const VOICEKI_API_URL = 'https://voice-ki-backend.onrender.com';
const VOICEKI_SECRET = process.env.VOICEKI_WEBHOOK_SECRET;

export async function processProtocol(
  protocol: ConversationProtocol
): Promise<ProcessProtocolResponse> {
  const response = await fetch(
    `${VOICEKI_API_URL}/webhook/process-protocol`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${VOICEKI_SECRET}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(protocol)
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Protocol processing failed: ${error.detail}`);
  }

  return await response.json();
}
```

---

## 🎨 **React Component**

```tsx
import { useState } from 'react';
import { processProtocol } from '@/api/voiceki';

export function ProtocolProcessor({ campaign }) {
  const [loading, setLoading] = useState(false);
  const [questions, setQuestions] = useState(null);

  async function handleProcess() {
    setLoading(true);
    try {
      const result = await processProtocol(campaign.transcript);
      setQuestions(result.questions);
      
      // Speichere Questions in HOC DB
      await saveCampaignQuestions(campaign.id, result.questions);
      
      toast.success(`✅ ${result.question_count} Fragen generiert!`);
    } catch (error) {
      toast.error('❌ Fehler beim Verarbeiten des Protocols');
    } finally {
      setLoading(false);
    }
  }

  return (
    <button onClick={handleProcess} disabled={loading}>
      {loading ? '⏳ Verarbeite...' : '🎙️ Questions generieren'}
    </button>
  );
}
```

---

## ✅ **Was der Service macht**

1. ✅ Empfängt Conversation Protocol
2. ✅ Generiert Questions automatisch mit OpenAI
3. ✅ Gibt nur Questions zurück (keine Speicherung)
4. ✅ HOC entscheidet, wo Questions gespeichert werden

---

## 🎯 **Vorteile**

- **Einfach:** Nur 1 Input, 1 Output
- **Schnell:** Keine DB-Operationen
- **Fokussiert:** Tut nur 1 Sache
- **Flexibel:** HOC hat volle Kontrolle

---

## 📊 **Question-Felder**

Jede generierte Question enthält:

```typescript
{
  id: string;              // Eindeutige ID
  question: string;        // Fragentext
  type: string;            // boolean, choice, string, etc.
  preamble?: string;       // Einleitung (optional)
  options?: string[];      // Antwortoptionen (bei choice)
  priority: number;        // 1=hoch, 2=mittel, 3=niedrig
  group?: string;          // Qualifikation, Rahmen, etc.
  help_text?: string;      // Hilfetext (optional)
  context?: string;        // Kontext-Info (optional)
  category?: string;       // standardqualifikationen, etc.
  category_order?: number; // Sortierung
}
```

**Keine internen Felder** wie `slot_config`, `gate_config`, etc.

---

## 🧪 **Testing**

### **cURL:**
```bash
curl -X POST https://voice-ki-backend.onrender.com/webhook/process-protocol \
  -H "Authorization: Bearer <WEBHOOK_SECRET>" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 62,
    "name": "Test Protocol",
    "pages": [{
      "id": 1,
      "name": "Qualifikationen",
      "position": 1,
      "prompts": [{
        "id": 1,
        "question": "Haben Sie einen Abschluss?",
        "position": 1
      }]
    }]
  }'
```

### **Response:**
```json
{
  "protocol_id": 62,
  "protocol_name": "Test Protocol",
  "processed_at": "2025-11-12T11:00:00Z",
  "question_count": 1,
  "questions": [...]
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

### **500 Internal Server Error**
```json
{
  "detail": "Protocol processing error: ..."
}
```
→ Protocol-Format prüfen oder Logs ansehen

---

## 📋 **Protocol-Format**

### **Pflichtfelder:**
- `id` (int): Protocol ID
- `name` (string): Protocol Name
- `pages` (array): Liste der Pages

### **Page-Format:**
- `id` (int): Page ID
- `name` (string): Page Name
- `position` (int): Reihenfolge
- `prompts` (array): Liste der Prompts

### **Prompt-Format:**
- `id` (int): Prompt ID
- `question` (string): Fragentext
- `position` (int): Reihenfolge

---

## 🎁 **Beispiel-Response**

```json
{
  "protocol_id": 62,
  "protocol_name": "Leitungskraft für unsere Kita",
  "processed_at": "2025-11-12T11:30:00Z",
  "question_count": 8,
  "questions": [
    {
      "id": "gate_staatlich_anerkannter_abschluss",
      "question": "Haben Sie einen staatlich anerkannten Abschluss in einem sozialpädagogischen Beruf?",
      "type": "boolean",
      "preamble": null,
      "options": null,
      "priority": 1,
      "group": "Qualifikation",
      "help_text": null,
      "context": "Muss-Kriterium: staatlich anerkannter Abschluss",
      "category": "standardqualifikationen",
      "category_order": 1
    },
    {
      "id": "gate_deutschkenntnisse_b2",
      "question": "Verfügen Sie über Deutschkenntnisse auf B2-Niveau?",
      "type": "boolean",
      "preamble": null,
      "options": null,
      "priority": 1,
      "group": "Qualifikation",
      "help_text": null,
      "context": "Muss-Kriterium: Deutschkenntnisse B2",
      "category": "standardqualifikationen",
      "category_order": 1
    },
    {
      "id": "arbeitszeit",
      "question": "Haben Sie bereits eine Präferenz bezüglich des Arbeitszeitmodells?",
      "type": "choice",
      "preamble": "Wir bieten Vollzeit (39 Wochenstunden) an.",
      "options": ["Vollzeit", "Teilzeit", "Bin noch flexibel"],
      "priority": 2,
      "group": "Rahmen",
      "help_text": null,
      "context": null,
      "category": "rahmenbedingungen",
      "category_order": 2
    }
  ]
}
```

---

## 📞 **Support**

- **Kontakt:** David (VoiceKI Tool)
- **API-URL:** https://voice-ki-backend.onrender.com
- **Logs:** Render.com Dashboard

---

## 🔄 **Versionen**

| Version | Beschreibung |
|---------|--------------|
| v1.0 | Campaign ID → Package (mit Storage) |
| v2.0 | Campaign ID + Daten → Package |
| **v3.0** | **Protocol → Questions (kein Storage)** ✅ |

**v3.0 ist die einfachste und empfohlene Version!**

---

**Version:** 3.0  
**Stand:** 12. November 2025  
**Status:** Production Ready ✅

