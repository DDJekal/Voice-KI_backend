# 🚀 VoiceKI - Quick Start Guide

**Bereit zum Testen!** Folge diesen Schritten um deinen ersten Voice-Agent Call zu starten.

---

## 📋 Voraussetzungen

✅ **Bereits erledigt:**
- Python Virtual Environment (`backend/venv/`)
- Alle Dependencies installiert
- ElevenLabs SDK + PyAudio
- Agent ID & API Key in `.env`

---

## 🎯 Option 1: Dry-Run (Empfohlen zum Start)

**Testet das komplette System ohne echten Call**

```bash
cd backend
venv\Scripts\python.exe test_dry_run.py
```

**Erwartet:**
```
✓ Knowledge Base: 28.496 Zeichen
✓ System Prompt: 2.334 Zeichen
✓ Call simuliert: mock_conv_...
✓ Output gespeichert
```

**Prüfe Output:**
```bash
dir Output_ordner\calls\
type Output_ordner\logs\call_orchestrator_*.log
```

---

## 🎙️ Option 2: WebRTC Test (Mit Mikrofon)

**Startet echten Agent-Call über dein Mikrofon**

```bash
cd backend
venv\Scripts\python.exe test_webrtc_conversation.py
```

**Was passiert:**
1. Script lädt Daten & baut Knowledge Base
2. Startet Mikrofon-Conversation
3. **Du sprichst** → Agent hört & antwortet
4. Drücke `Ctrl+C` zum Beenden

**⚠️ Wichtig:**
- Agent nutzt Dashboard-Konfiguration
- Dynamische KB wird IGNORIERT (nur für Tests)
- Stelle sicher: Mikrofon & Lautsprecher funktionieren

---

## 🔧 Troubleshooting

### Problem: "ELEVENLABS_API_KEY not set"
**Lösung:**
```bash
# Prüfe .env Datei im backend/ Ordner
notepad backend\.env
```

Sollte enthalten:
```env
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_AGENT_ID=agent_...
```

### Problem: "PyAudio import error"
**Lösung:**
```bash
cd backend
venv\Scripts\pip.exe install "elevenlabs[pyaudio]"
```

### Problem: "Agent antwortet nicht wie erwartet"
**Grund:** WebRTC nutzt Dashboard-Konfiguration, nicht deine KB

**Lösung:**
1. Öffne: https://elevenlabs.io/app/conversational-ai
2. Wähle deinen Agent
3. Bearbeite Knowledge Base & Prompts im Dashboard
4. Teste erneut

---

## 📊 Was getestet wird

### Dry-Run testet:
- ✅ Daten laden (Bewerber, Firma, Protokoll)
- ✅ Questions.json laden
- ✅ Daten aggregieren (4 Phasen)
- ✅ Knowledge Bases erstellen (28.496 Zeichen)
- ✅ Master Prompt laden (2.334 Zeichen)
- ✅ Mock Call simulieren
- ✅ Output speichern

### WebRTC testet:
- ✅ Alles vom Dry-Run
- ✅ Echten ElevenLabs API Call
- ✅ Audio I/O (Mikrofon/Lautsprecher)
- ✅ Agent-Interaktion
- ✅ Conversation Recording

---

## 🎨 Agent optimieren

**Nach WebRTC Test:**

1. **Dashboard öffnen:**
   https://elevenlabs.io/app/conversational-ai

2. **Agent auswählen:**
   Deine Agent ID: `agent_5101k8qg8trtec0b1bmkcnjk3e25`

3. **Optimieren:**
   - Knowledge Base anpassen
   - System Prompt verbessern
   - Voice & Sprache einstellen
   - Conversation Settings tunen

4. **Erneut testen:**
   ```bash
   venv\Scripts\python.exe test_webrtc_conversation.py
   ```

---

## 📞 Später: Telefon-Calls (Twilio)

**Aktuell:** WebRTC = Tests mit Mikrofon  
**Später:** Twilio = Echte Telefon-Anrufe

**Umstellung:**
```python
# Jetzt (WebRTC)
from src.telephony.webrtc_client import WebRTCConversation
client = WebRTCConversation(api_key)

# Später (Twilio)
from src.telephony.twilio_client import TwilioConversation
client = TwilioConversation(account_sid, auth_token, phone_number)

# Gleicher Orchestrator Code!
```

**Setup Twilio:**
1. Account erstellen: https://www.twilio.com/
2. Phone Number kaufen (~1€/Monat)
3. ElevenLabs Integration im Dashboard
4. `TwilioConversation` implementieren

---

## ✅ Checklist

- [ ] Dry-Run erfolgreich
- [ ] WebRTC Test erfolgreich
- [ ] Agent-Verhalten zufriedenstellend
- [ ] Dashboard-Konfiguration optimiert
- [ ] Bereit für Twilio Integration

---

## 🆘 Hilfe benötigt?

**Logs prüfen:**
```bash
type Output_ordner\logs\call_orchestrator_*.log
```

**Output prüfen:**
```bash
type Output_ordner\calls\mock_conv_*_kb.txt
type Output_ordner\calls\mock_conv_*_metadata.json
```

**Dokumentation:**
- `WEBRTC_INTEGRATION_COMPLETE.md` - Vollständige Integration
- `MODULAR_TRANSPORT_ARCHITECTURE.md` - Architektur
- `PROMPTS_INTEGRATION_COMPLETE.md` - Prompt-System

---

**Viel Erfolg! 🎉**

Bei Fragen oder Problemen: Logs & Output prüfen oder Dokumentation lesen.
