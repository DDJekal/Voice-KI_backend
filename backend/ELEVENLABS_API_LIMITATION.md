# ⚠️ ElevenLabs Voice Agents - API Limitierung

**Datum:** 29. Oktober 2025  
**Problem:** 405 Method Not Allowed Error

---

## 🔍 Problem-Analyse

### Was wir versucht haben:
```python
# REST API POST Request
endpoint = "https://api.elevenlabs.io/v1/conversational-ai/conversations"
response = requests.post(endpoint, json=payload)
# → 405 Method Not Allowed
```

### Was wir herausgefunden haben:

**ElevenLabs Voice Agents nutzen WebRTC, nicht REST API!**

Basierend auf dem ElevenLabs Python SDK (v2.20.1):
```
client.conversational_ai.conversations Methoden:
- get_webrtc_token  ← Für Browser-basierte WebRTC Connections
- get              ← Conversation Details abrufen
- list             ← Conversations auflisten
- delete           ← Conversation löschen
- audio            ← Audio-Daten abrufen
```

**Es gibt KEINE `create()` oder `start()` Methode!**

---

## 🎯 Was bedeutet das?

### Option 1: WebRTC für Browser-basierte Calls
Voice Agents sind **primär für Browser-basierte Conversations** gedacht:
1. User öffnet Webseite
2. Webseite holt WebRTC Token via API
3. Browser stellt WebRTC-Verbindung zum Agent her
4. Echtzeit-Conversation im Browser

**Nicht geeignet für:** Automatisierte Telefon-Anrufe ans Festnetz

### Option 2: Telefon-Integration (möglich)
Basierend auf den SDK-Methoden:
```
client.conversational_ai.phone_numbers  ← Telefonnummern Management
client.conversational_ai.twilio         ← Twilio Integration
client.conversational_ai.sip_trunk      ← SIP Trunk für Telefonie
```

**Das deutet darauf hin:** Telefon-Calls sind möglich, aber über:
- Twilio Integration (SIP-basiert)
- Eigene SIP-Trunk Integration
- ElevenLabs Telefonnummern

---

## 💡 Lösungsansätze

### Lösung A: Twilio Integration (empfohlen für Telefon-Calls)
1. ElevenLabs Agent mit Twilio verbinden
2. Twilio ruft Telefonnummern an
3. Agent führt Gespräch
4. Transkript über ElevenLabs API abrufen

**Setup:**
- Twilio Account benötigt
- Phone Number konfigurieren
- In ElevenLabs Dashboard: Agent → Integrations → Twilio

### Lösung B: WebRTC für Web-basierte Calls
Für Recruiting-Portal wo Bewerber im Browser anrufen:
1. Frontend mit WebRTC implementieren
2. Token via Backend API holen
3. Browser-basierte Voice Conversation

**Nicht geeignet für:** Outbound-Calls ans Telefon

### Lösung C: Warten auf ElevenLabs API Update
Möglicherweise wird ElevenLabs in Zukunft eine REST API für programmatische Calls anbieten.

---

## 📋 Nächste Schritte

### Empfohlener Workflow:

1. **Twilio Account erstellen**
   - https://www.twilio.com/
   - Phone Number kaufen

2. **ElevenLabs Dashboard öffnen**
   - Gehe zu deinem Agent
   - Integrations → Twilio
   - Verbinde Twilio Account

3. **Test-Call durchführen**
   - Twilio Dashboard: Outbound Call konfigurieren
   - Ziel-Nummer eingeben
   - Agent wird automatisch verbunden

4. **Transkripte abrufen**
   ```python
   # Via ElevenLabs API
   client = ElevenLabs(api_key=api_key)
   conversations = client.conversational_ai.conversations.list()
   
   for conv in conversations:
       transcript = client.conversational_ai.conversations.get(conv.id)
   ```

---

## 🔧 Code-Anpassungen erforderlich

### Aktueller Code (funktioniert NICHT):
```python
# backend/src/elevenlabs/voice_client.py
def start_conversation(...):
    # REST API Call → 405 Error
    response = requests.post(endpoint, ...)
```

### Benötigter Code (Twilio Integration):
```python
# Neuer Ansatz: Twilio-basierte Calls
def start_phone_call(phone_number: str, agent_id: str):
    # 1. Twilio Client
    from twilio.rest import Client
    twilio_client = Client(account_sid, auth_token)
    
    # 2. Call initiieren
    call = twilio_client.calls.create(
        to=phone_number,
        from_=twilio_phone_number,
        url=elevenlabs_webhook_url  # ElevenLabs Agent Webhook
    )
    
    return call.sid
```

---

## 📖 Dokumentation

- **ElevenLabs Docs:** https://elevenlabs.io/docs
- **Voice Agents:** https://elevenlabs.io/docs/quickstart (siehe "ElevenLabs Agents")
- **Twilio Integration:** Im ElevenLabs Dashboard unter Agent Settings

---

## ✅ Was funktioniert bereits

Unser aktuelles System kann:
- ✅ Master Prompt laden (2.334 Zeichen)
- ✅ Phase-Prompts integrieren (28.496 Zeichen KB)
- ✅ Knowledge Base generieren
- ✅ Variable Injection (Name, Adresse)
- ✅ Output-Speicherung
- ✅ Logging

**Was NICHT funktioniert:**
- ❌ Direkte REST API Calls für Voice Agents
- ❌ Automatisierte Telefon-Anrufe ohne Twilio

---

## 🎯 Empfehlung

**Für produktive Telefon-Recruiting:**

1. **Twilio Integration nutzen** (Standard-Weg für Telefonie)
2. **Oder:** ElevenLabs Team kontaktieren für Enterprise-Lösung
3. **Alternative:** Text-to-Speech API nutzen + eigene Call-Logik

**Für Web-basiertes Recruiting:**
- WebRTC Integration im Frontend implementieren
- Backend liefert nur Token + Knowledge Base

---

**Erstellt:** 29. Oktober 2025  
**Status:** API-Limitierung identifiziert  
**Lösung:** Twilio Integration erforderlich

