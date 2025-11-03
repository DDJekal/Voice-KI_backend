# Policy-Enhanced Knowledge Base System

## Übersicht

Das Policy-System erweitert die automatische Question-Generation um **intelligente Conversation-Policies**, die natürlichere und effektivere Voice-Gespräche ermöglichen.

### Was sind Policies?

Policies sind **regelbasierte Erweiterungen**, die Fragen automatisch mit zusätzlichen Metadaten anreichern:

- **Slot-Tracking**: Welche Information soll gesammelt werden?
- **Keyword-Triggers**: Welche Stichworte sollten Follow-up-Fragen auslösen?
- **Confidence-Checks**: Wie mit unklaren Antworten umgehen?
- **Diversification**: Vermeidung repetitiver Fragemuster
- **Gate-Sequencing**: Korrekte Reihenfolge von Must-Have-Kriterien
- **Empathy-Enhancement**: Empathische Reaktionen bei negativen Antworten

## Architektur

```
Conversation Protocol (Input)
        ↓
Question Generation (OpenAI)
        ↓
Base Questions
        ↓
[POLICY RESOLVER] ← NEU!
        ↓
Enhanced Questions (mit Slots, Hints, Triggers)
        ↓
Knowledge Base Builder
        ↓
Knowledge Base (mit Context-Rules)
```

### Pipeline-Integration

Der PolicyResolver ist als **Stage 6.5** in die Question-Builder-Pipeline integriert:

1. Extract (LLM)
2. Structure
3. Conversational Flow
4. Expand
5. Validate
6. Categorize
7. **Apply Policies** ← NEU
8. Generate Catalog

## Policy-Level

Das System bietet drei Komplexitätsstufen:

### Basic (3 Policies)

Minimale Enhancements für grundlegende Gesprächsführung:

- ✅ **Consent-First**: DSGVO-Fragen immer zuerst
- ✅ **Slot-Dependencies**: Pflicht-Slots priorisieren
- ✅ **Gate-Sequence**: Gates vor anderen Fragen

**Verwendung:**
```bash
python setup_campaign.py --campaign-id 16 --policy-level basic
```

### Standard (6 Policies) ⭐ **Default**

Empfohlene Konfiguration für Production:

- ✅ Basic-Policies (3)
- ✅ **Keyword-Triggers**: Proaktive Reaktion auf Schlüsselwörter
- ✅ **Diversification**: Vermeidung repetitiver Fragen
- ✅ **Confidence-Checks**: Rückfragen bei Unsicherheit

**Verwendung:**
```bash
python setup_campaign.py --campaign-id 16
# oder explizit:
python setup_campaign.py --campaign-id 16 --policy-level standard
```

### Advanced (7+ Policies)

Maximale Intelligenz für komplexe Gespräche:

- ✅ Standard-Policies (6)
- ✅ **Empathy-Enhancement**: Empathische Reaktionen
- ✅ Zusätzliche domänenspezifische Policies

**Verwendung:**
```bash
python setup_campaign.py --campaign-id 16 --policy-level advanced
```

## Output-Änderungen

### questions.json - Vorher

```json
{
  "id": "kriterium_pflegefachkraft",
  "question": "Sind Sie examinierte Pflegefachkraft?",
  "type": "boolean",
  "required": true,
  "priority": 1,
  "category": "standardqualifikationen"
}
```

### questions.json - Nachher (mit Policies)

```json
{
  "id": "kriterium_pflegefachkraft",
  "question": "Sind Sie examinierte Pflegefachkraft?",
  "type": "boolean",
  "required": true,
  "priority": 1,
  "category": "standardqualifikationen",
  
  "slot_config": {
    "fills_slot": "qualifikation_pflege",
    "required": true,
    "confidence_threshold": 0.85
  },
  
  "gate_config": {
    "is_gate": true,
    "requires_slots": ["qualifikation_pflege"],
    "context_triggers": {
      "keywords_to_follow_up": ["Intensiv", "IMC", "ITS"]
    }
  },
  
  "conversation_hints": {
    "on_unclear_answer": "Verstehe ich richtig, dass Sie {interpretation}?",
    "confidence_boost_phrases": ["ja", "examiniert", "Examen"]
  }
}
```

### Knowledge Base - Vorher

```
======================================================================
STANDARDQUALIFIKATIONEN (GATE)
======================================================================

FRAGE-ID: kriterium_pflegefachkraft
Typ: boolean
Pflicht: JA

Frage:
Sind Sie examinierte Pflegefachkraft?
```

### Knowledge Base - Nachher (mit Context-Rules)

```
======================================================================
STANDARDQUALIFIKATIONEN (GATE)
======================================================================

FRAGE-ID: kriterium_pflegefachkraft
Typ: boolean
Pflicht: JA

Frage:
Sind Sie examinierte Pflegefachkraft?

============================================================
✨  SLOT-TRACKING
============================================================
▸ Füllt Slot: qualifikation_pflege
▸ Erforderlich: JA
▸ Confidence-Schwelle: 0.85

============================================================
⚠️  GATE-LOGIK
============================================================
▸ Dies ist eine Gate-Question
▸ Benötigt Slots: qualifikation_pflege

▸ KEYWORD-TRIGGER:
  Wenn Kandidat erwähnt: Intensiv, IMC, ITS
  → Sofort vertiefen und nachfragen!

============================================================
💬  GESPRÄCHSFÜHRUNG
============================================================
▸ Bei unklarer Antwort:
  "Verstehe ich richtig, dass Sie {interpretation}?"

▸ Klare Signale: ja, examiniert, Examen

---

🧠  KONTEXT-REGELN FÜR NATÜRLICHE GESPRÄCHSFÜHRUNG
======================================================================

1. KEYWORD-SENSITIVITÄT (reagiere proaktiv!):
   • "Intensiv" erwähnt → Sofort vertiefen!

2. CONFIDENCE & SLOT-TRACKING:
   Erforderliche Slots für Phase 3:
     ✓ qualifikation_pflege (MUSS geklärt sein)
     ✓ standort_praeferenz (MUSS geklärt sein)
     
3. GATE-SEQUENZ (strikt einhalten!):
   [...]
```

## A/B-Testing

Das System unterstützt A/B-Testing durch einfaches Deaktivieren der Policies:

### Kontrollgruppe (ohne Policies)

```bash
python setup_campaign.py --campaign-id test1 --no-policies
```

### Testgruppe (mit Policies)

```bash
python setup_campaign.py --campaign-id test2 --enable-policies
```

### Vergleich

```bash
# Vergleiche die generierten Outputs
diff backend/campaign_packages/test1.json backend/campaign_packages/test2.json
```

**Messbare KPIs:**
- Call-Completion-Rate
- Durchschnittliche Call-Dauer
- Slot-Fill-Rate (Vollständigkeit der Daten)
- Candidate-Satisfaction-Score
- Vorzeitige Abbrüche

## Verwendung

### Setup einer Campaign

```bash
# Standard (mit Policies)
python setup_campaign.py --campaign-id 16

# Mit spezifischem Level
python setup_campaign.py --campaign-id 16 --policy-level advanced

# Ohne Policies (A/B-Testing)
python setup_campaign.py --campaign-id 16 --no-policies
```

### Testing

```bash
# Test mit Standard-Policies
python test_question_generator.py 16

# Test mit Advanced-Policies
python test_question_generator.py 16 --policy-level advanced

# Test ohne Policies
python test_question_generator.py 16 --policy-level none
```

### API-Integration

```python
from src.campaign.package_builder import CampaignPackageBuilder

# Mit Policies
builder = CampaignPackageBuilder(
    prompts_dir=Path("../VoiceKI _prompts"),
    policy_config={
        "enabled": True,
        "level": "standard"
    }
)

# Ohne Policies
builder = CampaignPackageBuilder(
    prompts_dir=Path("../VoiceKI _prompts"),
    policy_config={
        "enabled": False
    }
)

package = await builder.build_package(campaign_id, api_source)
```

## Implementierte Policies im Detail

### 1. Consent-First Policy

**Zweck:** DSGVO-Compliance sicherstellen

**Regel:** Jede Frage mit Keywords wie "DSGVO", "Einwilligung", "Datenschutz" erhält:
- Höchste Priorität (1)
- Category-Order: 0 (kommt zuerst)
- Slot: `consent_given` (required)
- Confidence-Threshold: 0.95

**Beispiel:**
```python
# Vorher
{"id": "dsgvo_consent", "priority": 2, "required": true}

# Nachher
{"id": "dsgvo_consent", "priority": 1, "category_order": 0, 
 "slot_config": {"fills_slot": "consent_given", "required": true}}
```

### 2. Slot-Dependency Policy

**Zweck:** Systematisches Tracking erforderlicher Informationen

**Regel:** Pflichtfragen werden automatisch Slots zugeordnet:
- `qualifikation`: "examen", "pflegefach", "ausbildung"
- `standort`: "standort", "einsatzort"
- `verfuegbarkeit`: "verfügbar", "starten", "beginn"
- `dienstmodell`: "vollzeit", "teilzeit"

**Beispiel:**
```python
# Frage enthält "examen" → Slot "qualifikation" wird zugeordnet
{"slot_config": {"fills_slot": "qualifikation", "required": true}}
```

### 3. Gate-Sequence Policy

**Zweck:** Kritische Kriterien vor Präferenzen klären

**Regel:** 
- Alle Gate-Fragen erhalten Priority 1
- Category: "standardqualifikationen" (Order 3)
- Slot-Requirements werden hinzugefügt
- Confidence-Threshold: 0.9

**Effekt:** Gates werden garantiert vor Rahmenbedingungen gefragt

### 4. Keyword-Trigger Policy

**Zweck:** Proaktive Reaktion auf wichtige Stichworte

**Regel:** Domänenspezifische Keywords auslösen Follow-ups:
- "Intensiv", "IMC", "ITS" → Vertiefung Intensiv-Erfahrung
- "Teilzeit" → Klärung Stunden/Woche
- "Nachtdienst" → Schichtmodell-Frage vorziehen

**Beispiel:**
```python
"gate_config": {
  "context_triggers": {
    "keywords_to_follow_up": ["Intensiv", "IMC", "ITS"]
  }
}
```

### 5. Diversification Policy

**Zweck:** Monotone Fragemuster vermeiden

**Regel:**
- Zählt aufeinanderfolgende boolean-Fragen
- Nach 2+ booleans: Hint "diversify_after": "boolean"
- ElevenLabs kann dann Infos einstreuen oder Fragetyp wechseln

**Effekt:** Natürlicherer Gesprächsfluss

### 6. Confidence-Check Policy

**Zweck:** Umgang mit unklaren Antworten

**Regel:** Für required-Fragen werden hinzugefügt:
- `on_unclear_answer`: Rückfrage-Template
- `confidence_boost_phrases`: Klare Signal-Wörter
- Schwelle: < 0.8 → Rückfrage

**Beispiel:**
```python
"conversation_hints": {
  "on_unclear_answer": "Verstehe ich richtig, dass Sie {interpretation}?",
  "confidence_boost_phrases": ["ja", "definitiv", "sicher"]
}
```

### 7. Empathy-Enhancement Policy (Advanced)

**Zweck:** Empathische Reaktionen bei Ablehnung

**Regel:** Für Gate-Fragen werden empathische Antworten hinzugefügt:
- Gate-NEIN: "Vielen Dank für Ihre Offenheit. Lassen Sie uns eine Alternative prüfen."
- Präferenz-NEIN: "Kein Problem, das verstehe ich gut."

**Effekt:** Bessere Candidate-Experience

## Custom Policies

Das System ist erweiterbar. Neue Policies können hinzugefügt werden:

### Beispiel: Domain-Specific Policy

```python
# In policy_resolver.py
def _healthcare_specific_policy(self, questions):
    """Spezielle Regeln für Gesundheitswesen"""
    for q in questions:
        if "hygiene" in q.question.lower():
            q.priority = 1
            if not q.gate_config:
                q.gate_config = GateConfig()
            q.gate_config.context_triggers = {
                "keywords_to_follow_up": ["Desinfektion", "Sterilisation"]
            }
    return questions
```

## Bekannte Einschränkungen

1. **ElevenLabs Autonomie**: Da ElevenLabs autonom agiert, sind Policies **Empfehlungen** in der KB, keine harten Regeln.

2. **Keine Live-Kontrolle**: Backend ist nicht im Loop während des Calls. Policies müssen **vor** dem Call in der KB kodiert sein.

3. **LLM-Interpretation**: Die Policies sind natürlichsprachlich formuliert. Qualität hängt von ElevenLabs' Interpretation ab.

## Best Practices

### ✅ DO

- Standard-Level für Production nutzen
- A/B-Testing mit `--no-policies` durchführen
- Policy-Audit-Logs überwachen (`_meta.policies_applied`)
- Domain-Packs für Wiederverwendung erstellen

### ❌ DON'T

- Advanced-Level ohne Testing einsetzen
- Policies als harte Garantien verstehen
- System ohne A/B-Vergleich optimieren
- Zu viele Custom-Policies ohne Dokumentation

## Troubleshooting

### Policies werden nicht angewendet

**Problem:** `_meta.policies_applied` ist `null`

**Lösung:** 
```bash
# Prüfe ob Policy-Level übergeben wird
python setup_campaign.py --campaign-id 16 --policy-level standard
```

### KB enthält keine Context-Rules

**Problem:** Context-Rules-Sektion fehlt

**Ursache:** Policies sind deaktiviert oder `_meta.policies_applied` ist leer

**Lösung:** Stelle sicher, dass Policies aktiviert sind

### Zu viele/wenige Enhancements

**Problem:** Alle Fragen haben Slots/Hints

**Lösung:** Passe Policy-Level an:
- Zu viel → Basic
- Zu wenig → Advanced

## Versionierung

- **v1.0** (2025-11): Initial Release
  - 6 Standard-Policies
  - 3 Policy-Level
  - A/B-Testing Support

## Support

Bei Fragen oder Problemen:
1. Prüfe dieses Dokument
2. Teste mit verschiedenen Policy-Levels
3. Vergleiche Output mit/ohne Policies
4. Kontaktiere Team bei Unklarheiten

## Roadmap

Geplante Features:

- [ ] Post-Call-Analyse (Phase 2)
- [ ] Live-Resolver für Custom Voice-Providers (Phase 3)
- [ ] ML-basierte Policy-Optimierung
- [ ] Domain-spezifische Policy-Packs (Pflege, Therapie, Finance)
- [ ] Policy-Templates für häufige Use-Cases

