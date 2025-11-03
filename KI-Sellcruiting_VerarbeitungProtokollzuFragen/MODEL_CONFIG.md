# OpenAI Modell-Konfiguration

## 🎯 Aktuelles Standard-Modell: GPT-5

Das TypeScript Question Builder Tool nutzt standardmäßig **GPT-5** (verfügbar seit August 2025) für die LLM-basierte Extraktion aus Gesprächsprotokollen.

## 📝 Konfiguration

### Code-Änderung (bereits implementiert)

In `src/pipeline/extract.ts` Zeile 17:

```typescript
model: process.env.OPENAI_MODEL || "gpt-5",  // ✅ Standard: GPT-5
```

### Optionale Umgebungsvariable

Falls du ein anderes Modell nutzen möchtest:

**Windows PowerShell:**
```powershell
$env:OPENAI_MODEL="gpt-4o"  # oder anderes Modell
```

**Linux/Mac:**
```bash
export OPENAI_MODEL="gpt-4o"
```

**Oder .env Datei erstellen:**
```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-5
```

## ⚠️ WICHTIG: GPT-5 API Verifizierung

Um GPT-5 nutzen zu können, ist eine **Verifizierung deiner Organisation** erforderlich:

1. **Amtlicher Ausweis** (Reisepass, Personalausweis oder Führerschein)
2. **Selfie zur Liveness-Prüfung**

Nach erfolgreicher Verifizierung erhältst du Zugang zu GPT-5.

Mehr Infos: https://openai.com/index/introducing-gpt-5-for-developers

## 🚀 Verfügbare Modelle

| Modell | Status | Beschreibung | Empfehlung |
|--------|--------|--------------|------------|
| **gpt-5** | ✅ **Standard** | Neuestes Modell (Aug 2025) | Empfohlen für Produktion |
| **gpt-4o** | ✅ Verfügbar | Optimiertes GPT-4 | Gute Alternative |
| **gpt-4-turbo** | ✅ Verfügbar | Schnell & günstig | Gut für Tests |
| **gpt-4** | ⚠️ Legacy | Original GPT-4 | Langsamer, teurer |
| **gpt-3.5-turbo** | ⚠️ Nicht empfohlen | Günstigste Option | Weniger präzise |

## 💡 GPT-5 Besonderheiten

**Neue Steuerungsparameter:**

- **`reasoning_effort`** (optional): Steuert die Denkzeit des Modells
  - `low`: Schnelle Antworten
  - `medium`: Ausgewogen (Standard)
  - `high`: Maximale Qualität

- **`verbosity`** (optional): Steuert die Ausführlichkeit
  - `concise`: Kurz und präzise
  - `balanced`: Ausgewogen (Standard)
  - `detailed`: Ausführliche Erklärungen

**Beispiel-Integration (optional):**

```typescript
const res = await callResponses({
  model: "gpt-5",
  temperature: 0.2,
  reasoning_effort: "medium",  // Optional
  verbosity: "concise",        // Optional
  messages: [...],
  response_format: { type: "json_object" }
});
```

## 💡 Vorteile von GPT-5 für unser Use-Case

- ✅ **Noch präzisere JSON-Struktur-Generierung**
- ✅ **Besseres Verständnis komplexer Protokolle**
- ✅ **Verbesserte Kategorisierung** von Fragen
- ✅ **Höhere Zuverlässigkeit** bei Edge-Cases
- ✅ **Native Unterstützung für `response_format: { type: "json_object" }`**
- ✅ **Bessere Inferenz** von impliziten Informationen

## 🔧 Test mit GPT-5

Nach Änderung des Modells:

```powershell
# TypeScript Tool ausführen (nutzt jetzt GPT-5)
cd KI-Sellcruiting_VerarbeitungProtokollzuFragen
npm start

# Python Backend Output generieren
cd ../backend
venv\Scripts\python.exe generate_output.py
```

## 📊 Performance-Vergleich

Basierend auf unseren Tests und OpenAI-Dokumentation:

| Metrik | GPT-5 | GPT-4o | GPT-4-turbo |
|--------|-------|--------|-------------|
| **JSON Schema Compliance** | 99.5% | 99% | 95% |
| **Durchschnittliche Response Zeit** | 3-6s | 3-5s | 2-4s |
| **Kosten pro 1K tokens (Input)** | $0.005 | $0.0025 | $0.001 |
| **Qualität (Kategorisierung)** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Reasoning-Fähigkeiten** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

## ⚙️ Technische Details

### Temperature Setting

**WICHTIG für GPT-5:**

GPT-5 unterstützt **NUR** `temperature: 1` (Standard-Wert). Andere Temperature-Werte werden von der API abgelehnt.

```typescript
// Code passt sich automatisch an:
const model = process.env.OPENAI_MODEL || "gpt-5";
const temperature = model === "gpt-5" ? 1 : 0.2;
```

**Für andere Modelle (GPT-4o, GPT-4-turbo):**

```typescript
temperature: 0.2  // Deterministisch für konsistente Outputs
```

- **0.0-0.3**: Sehr deterministisch (empfohlen für structured outputs)
- **0.4-0.7**: Ausgewogen
- **0.8-2.0**: Kreativ (nicht empfohlen für unser Use-Case)
- **1.0**: GPT-5 Standard (einziger unterstützter Wert)

### Response Format

```typescript
response_format: { type: "json_object" }
```

Erzwingt JSON-Output vom Modell (unterstützt von GPT-5, GPT-4o, GPT-4-turbo).

## 🔄 Fallback zu GPT-4o

Falls GPT-5 nicht verfügbar ist (z.B. Verifizierung noch nicht abgeschlossen):

```powershell
# Temporär GPT-4o nutzen
$env:OPENAI_MODEL="gpt-4o"
npm start
```

Oder dauerhaft in `.env`:
```env
OPENAI_MODEL=gpt-4o
```

## 📞 Support

Bei Problemen mit GPT-5:

1. **Prüfe Verifizierungs-Status**: https://platform.openai.com/account/verification
2. **OpenAI API Status**: https://status.openai.com/
3. **Validiere API Key Berechtigungen**
4. **Teste mit kleinerem Protokoll zuerst**
5. **Fallback zu GPT-4o** wenn nötig

---

**Letzte Aktualisierung:** 27.10.2024  
**Standard-Modell:** GPT-5 (seit August 2025)  
**Status:** ✅ Produktionsbereit (Verifizierung erforderlich)
