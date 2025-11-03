# Deployment Checklist - VoiceKI Backend

**Für:** Server-Deployment (AWS, Azure, Heroku, etc.)  
**Status:** Ready for Production

---

## 📋 Pre-Deployment Checklist

### 1. System Requirements

- [ ] Python 3.9 oder höher
- [ ] pip installiert
- [ ] git installiert (optional, für Repository-Zugriff)
- [ ] Netzwerk-Zugriff zur API
- [ ] Netzwerk-Zugriff zu ElevenLabs API

### 2. Dependencies

Erstelle Virtual Environment und installiere Dependencies:

```bash
cd backend

# Virtual Environment erstellen
python3 -m venv venv

# Aktivieren (Linux/Mac)
source venv/bin/activate

# Aktivieren (Windows)
venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt
```

**requirements.txt muss enthalten:**
```
requests>=2.31.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
elevenlabs>=1.0.0
```

### 3. Environment Variables

Erstelle `.env` Datei im `backend/` Verzeichnis:

```env
# ElevenLabs Configuration
ELEVENLABS_API_KEY=sk_your_actual_api_key_here
ELEVENLABS_AGENT_ID=agent_your_actual_agent_id_here

# API Data Source
USE_API_SOURCE=true
API_URL=https://your-production-api-url.com
API_KEY=your_actual_api_key_here

# Optional: OpenAI (für TypeScript Tool)
OPENAI_API_KEY=sk-your_openai_key_here

# Operational Settings
DRY_RUN=false
GENERATE_QUESTIONS=false
```

**⚠️ WICHTIG:** 
- Verwende echte Production Keys
- Nie `.env` ins Git committen!
- Prüfe `.gitignore` enthält `.env`

---

## 🚀 Deployment Steps

### Option A: Manuelles Deployment

#### 1. Code auf Server kopieren

```bash
# Via Git
git clone https://github.com/your-repo/voiceki.git
cd voiceki/backend

# Oder via SCP
scp -r backend/ user@server:/path/to/voiceki/
```

#### 2. Setup auf Server

```bash
ssh user@server
cd /path/to/voiceki/backend

# Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env erstellen
nano .env
# → Füge Production Keys ein
```

#### 3. Test-Run

```bash
# Test API-Verbindung
python test_api_source.py

# Test einzelner Call (Dry-Run)
python main.py --applicant-id "test" --campaign-id "1" --dry-run

# Test echter Call
python main.py --applicant-id "+49 1234..." --campaign-id "16"
```

### Option B: Docker Deployment

#### Dockerfile erstellen

**Datei:** `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Environment variables (überschreibbar)
ENV USE_API_SOURCE=true
ENV DRY_RUN=false

# Expose (falls FastAPI später hinzukommt)
# EXPOSE 8000

# Entry point
CMD ["python", "process_all_applicants.py"]
```

#### Docker Build & Run

```bash
# Build
docker build -t voiceki-backend .

# Run mit .env
docker run --env-file .env voiceki-backend

# Run mit einzelnen Envs
docker run \
  -e API_URL=https://api.example.com \
  -e API_KEY=xxx \
  -e ELEVENLABS_API_KEY=sk_xxx \
  -e ELEVENLABS_AGENT_ID=agent_xxx \
  voiceki-backend
```

### Option C: Serverless (AWS Lambda)

#### Lambda Function Setup

**Datei:** `backend/lambda_handler.py`

```python
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.data_sources.api_loader import APIDataSource
from src.orchestrator.call_orchestrator import CallOrchestrator
# ... imports

def lambda_handler(event, context):
    """
    AWS Lambda Handler für Batch-Processing.
    
    Trigger: CloudWatch Events (Cron)
    Frequenz: z.B. alle 15 Minuten
    """
    
    # Initialisiere
    settings = get_settings()
    api = APIDataSource(settings.api_url, settings.api_key)
    orchestrator = CallOrchestrator(...)
    
    # Verarbeite alle Bewerber
    applicants = api.list_pending_applicants()
    results = []
    
    for applicant in applicants:
        try:
            result = orchestrator.start_call(...)
            results.append({"success": True, "applicant": applicant})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
    
    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }
```

**Lambda Configuration:**
- Runtime: Python 3.11
- Timeout: 15 Minuten (max)
- Memory: 512 MB
- Environment Variables: Alle aus `.env`

**CloudWatch Event Rule:**
```
Schedule Expression: rate(15 minutes)
Target: Lambda Function
```

---

## ⚙️ Automation & Scheduling

### Cron Job (Linux/Mac)

```bash
# Crontab bearbeiten
crontab -e

# Alle 15 Minuten ausführen
*/15 * * * * cd /path/to/voiceki/backend && venv/bin/python process_all_applicants.py >> /var/log/voiceki.log 2>&1

# Jeden Morgen um 9 Uhr
0 9 * * * cd /path/to/voiceki/backend && venv/bin/python process_all_applicants.py >> /var/log/voiceki.log 2>&1
```

### Systemd Service (Linux)

**Datei:** `/etc/systemd/system/voiceki-batch.service`

```ini
[Unit]
Description=VoiceKI Batch Processing
After=network.target

[Service]
Type=oneshot
User=voiceki
WorkingDirectory=/path/to/voiceki/backend
Environment="PATH=/path/to/voiceki/backend/venv/bin"
ExecStart=/path/to/voiceki/backend/venv/bin/python process_all_applicants.py

[Install]
WantedBy=multi-user.target
```

**Datei:** `/etc/systemd/system/voiceki-batch.timer`

```ini
[Unit]
Description=VoiceKI Batch Processing Timer

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
```

**Aktivieren:**
```bash
sudo systemctl enable voiceki-batch.timer
sudo systemctl start voiceki-batch.timer
```

### Windows Task Scheduler

1. Task Scheduler öffnen
2. "Neue Aufgabe erstellen"
3. **Trigger:** Alle 15 Minuten
4. **Aktion:** 
   - Programm: `C:\path\to\voiceki\backend\venv\Scripts\python.exe`
   - Argumente: `process_all_applicants.py`
   - Starten in: `C:\path\to\voiceki\backend`

---

## 🔒 Security

### 1. API Keys schützen

```bash
# .env Berechtigungen (nur Owner lesen)
chmod 600 .env

# Nie ins Git
echo ".env" >> .gitignore
```

### 2. Firewall Regeln

**Ausgehend (Outbound):**
- ElevenLabs API: `api.elevenlabs.io` (HTTPS/443)
- Eure API: `your-api-url.com` (HTTPS/443)

**Eingehend (Inbound):**
- Nur SSH (22) für Administration
- Keine öffentlichen Ports nötig (Backend ist Client, nicht Server)

### 3. Secrets Management

**AWS Secrets Manager:**
```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# In config.py
secrets = get_secret('voiceki/production')
elevenlabs_api_key = secrets['ELEVENLABS_API_KEY']
```

---

## 📊 Monitoring & Logging

### 1. Logging Setup

**Datei:** `backend/src/utils/logger.py` (bereits vorhanden)

Logs werden geschrieben nach: `backend/Output_ordner/logs/`

### 2. Log Rotation

**Linux (logrotate):**

**Datei:** `/etc/logrotate.d/voiceki`

```
/path/to/voiceki/backend/Output_ordner/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

### 3. Monitoring

**Einfach:**
- Cron sendet Email bei Fehler
- Logs regelmäßig prüfen

**Erweitert:**
- CloudWatch Logs (AWS)
- Datadog
- Sentry für Error Tracking

---

## 🧪 Testing in Production

### Smoke Test

```bash
# 1. API-Verbindung testen
python test_api_source.py

# 2. Einzelnen Call testen
python main.py --applicant-id "test_number" --campaign-id "test_id"

# 3. Batch-Processing (limitiert)
# → Implementiere --limit Flag für Tests
```

### Health Check Script

**Datei:** `backend/health_check.py`

```python
import sys
from src.config import get_settings
from src.data_sources.api_loader import APIDataSource

def health_check():
    settings = get_settings()
    
    # Check API
    try:
        api = APIDataSource(settings.api_url, settings.api_key)
        applicants = api.list_pending_applicants()
        print(f"✅ API OK: {len(applicants)} applicants")
    except Exception as e:
        print(f"❌ API FAIL: {e}")
        sys.exit(1)
    
    # Check ElevenLabs
    # ...
    
    print("✅ All systems operational")

if __name__ == "__main__":
    health_check()
```

---

## 🚨 Troubleshooting

### Problem: "Module not found"
**Lösung:** 
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Problem: "API Connection Timeout"
**Lösung:**
- Prüfe Firewall
- Prüfe API_URL korrekt
- Teste: `curl https://your-api-url.com/applicants/new`

### Problem: "ElevenLabs Rate Limit"
**Lösung:**
- Batch-Processing langsamer machen
- Pause zwischen Calls: `time.sleep(5)`
- Upgrade ElevenLabs Plan

---

## 📈 Scaling

### Horizontal Scaling

**Option 1: Mehrere Worker**
```bash
# Worker 1: Bewerber 1-100
python process_all_applicants.py --range 0-100

# Worker 2: Bewerber 101-200
python process_all_applicants.py --range 100-200
```

**Option 2: Queue-basiert (Celery)**
- Redis/RabbitMQ als Message Queue
- Celery Workers verarbeiten Jobs parallel

---

## ✅ Go-Live Checklist

- [ ] Python 3.9+ installiert
- [ ] Virtual Environment erstellt
- [ ] Dependencies installiert
- [ ] .env mit Production Keys
- [ ] API-Verbindung getestet
- [ ] ElevenLabs-Verbindung getestet
- [ ] Test-Call erfolgreich
- [ ] Logging funktioniert
- [ ] Cron Job/Scheduler konfiguriert
- [ ] Monitoring aktiv
- [ ] Firewall-Regeln gesetzt
- [ ] Backup-Strategie definiert

---

## 📞 Support

Bei Problemen:
1. Prüfe Logs: `backend/Output_ordner/logs/`
2. Führe Health Check aus: `python health_check.py`
3. Teste API einzeln: `python test_api_source.py`

---

**Version:** 1.0  
**Letzte Aktualisierung:** November 2025  
**Status:** Production Ready

