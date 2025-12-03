# 🎯 Campaign Package Analyse: Campaign 258 (Pflegefachkräfte)

## ✅ ERFOLGREICH GENERIERT

**Company:** Wege Klinik GmbH  
**Campaign:** Pflegefachkräfte  
**Generated:** 2025-11-03 13:23:25  
**Policy Level:** standard

---

## 📊 DATENQUELLEN-INTEGRATION

### 1️⃣ Gesprächsprotokoll (Conversation Protocol) → Questions

**Quelle:** `campaign.transcript` aus API  
**Verwendung:** Generierung von `questions.json` mit OpenAI

**Generierte Fragen (8):**
- ✅ name_confirmation (mit Slot: `name`)
- ✅ address_confirmation (mit Slot: `address`)
- ✅ address_request (mit Slot: `address`)
- ✅ site_confirmation (mit Slot: `standort`)
- ✅ gate_examinierter_gesundheits_und_krankenpfleger
- ✅ gate_bereitschaft_zu_schichtdienst (mit Slot: `schichtmodell`)
- ✅ arbeitszeit (mit Slot: `dienstmodell`)
- ✅ start_date (mit Slot: `verfuegbarkeit`)

**Policy Enhancements:**
- 21 Policies angewendet
- 8 Fragen mit Slot-Tracking
- 9 Fragen mit Conversation-Hints
- 3 Fragen mit Keyword-Triggers

---

### 2️⃣ Unternehmensprofil (Onboarding) → Knowledge Base

**Quelle:** `company.onboarding` aus API  
**Verwendung:** KB-Templates für Phase 2 & 4

**Integrierte Daten:**
- ✅ `{{companyname}}` = Wege Klinik GmbH
- ✅ `{{companysize}}` = Mitarbeiterzahl aus Onboarding
- ✅ `{{companypitch}}` = Benefits/Vorteile aus Onboarding
- ✅ `{{companypriorities}}` = Schwerpunkte (z.B. Palliativ)
- ✅ `{{campaignlocation_label}}` = Villenstr. 8, 53129 Bonn

**Verwendung in KB-Templates:**
- **Phase 1:** Begrüßung mit Unternehmensnamen
- **Phase 2:** Vollständige Unternehmensvorstellung mit Onboarding-Daten
- **Phase 3:** Fragen aus Gesprächsprotokoll mit Policy-Hints
- **Phase 4:** Verabschiedung mit Company-Kontext

---

## 📦 GENERIERTES PACKAGE

**Struktur:**
```json
{
  "campaign_id": "258",
  "company_name": "Wege Klinik GmbH",
  "campaign_name": "Pflegefachkräfte",
  "questions": { /* 8 Fragen mit Policies */ },
  "kb_templates": {
    "phase_1": "5703 Zeichen",
    "phase_2": "3583 Zeichen (mit Onboarding-Daten!)",
    "phase_3": "12597 Zeichen (mit Gesprächsprotokoll!)",
    "phase_4": "3449 Zeichen"
  },
  "priorities": [],
  "metadata": { /* Campaign-Metadaten */ }
}
```

---

## 🔍 BEISPIEL: PHASE 2 (Unternehmensvorstellung)

```
„{{companyname}} mit rund {{companysize}} Mitarbeitenden in {{campaignlocation_label}}."

„Wir bieten {{companypitch}}." (komprimiert: wähle 2–3 stärkste Aspekte)

„Aktuell wichtig für uns: {{companypriorities}}." 
```

→ **Verwendet Daten aus `company.onboarding.pages.prompts`**

---

## 🔍 BEISPIEL: PHASE 3 (Qualifikations-Fragen)

```json
{
  "id": "gate_examinierter_gesundheits_und_krankenpfleger",
  "question": "Haben Sie: examinierter Gesundheits- und Krankenpfleger?",
  "slot_config": null,
  "gate_config": {
    "context_triggers": {
      "keywords_to_follow_up": ["IMC", "Intensiv", "ITS"]
    }
  },
  "conversation_hints": {
    "on_unclear_answer": "Verstehe ich richtig, dass Sie {interpretation}?",
    "confidence_boost_phrases": ["ja", "definitiv", "sicher", ...]
  }
}
```

→ **Verwendet Daten aus `campaign.transcript.pages.prompts`**  
→ **Erweitert mit Policy-System (Keyword-Triggers, Hints)**

---

## ✅ FAZIT

**BEIDE DATENQUELLEN WERDEN VOLLSTÄNDIG INTEGRIERT:**

1. ✅ **Gesprächsprotokoll** → Questions mit intelligenten Policies
2. ✅ **Unternehmensprofil (Onboarding)** → Knowledge Base Templates
3. ✅ Policy-System erweitert Fragen mit:
   - Slot-Tracking für Datenerfassung
   - Conversation-Hints für natürliche Gesprächsführung
   - Keyword-Triggers für kontextuelle Follow-ups

**Das System ist PRODUKTIONSBEREIT! 🚀**

---

## 📁 GESPEICHERT

**Package:** `campaign_packages/258.json`

**Verwendung:**
- Wird über Webhook an HOC hochgeladen
- HOC verwendet die KBs für ElevenLabs Agent
- ElevenLabs führt autonome Gespräche basierend auf den Templates

