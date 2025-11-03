import type { ExtractResult, CandidateProfile, Question } from "../types";
import { slug } from "../utils/text";

/**
 * Builds questions with {{variable}} templates for applicant data.
 * This mode is used for campaign templates - no actual applicant data is required.
 */
export function buildQuestionsTemplate(extr: ExtractResult): Question[] {
  const q: Question[] = [];

  // === CONTACT & IDENTIFICATION (with {{variables}}) ===
  
  // Name confirmation (always with template)
  q.push({
    id: "name_confirmation",
    question: "Spreche ich mit {{candidatefirst_name}} {{candidatelast_name}}?",
    type: "boolean",
    required: true,
    priority: 1,
    group: "Kontakt",
    source: { verbatim: false },
    context: "Identifikation des Bewerbers"
  });

  // Address confirmation (always with template)
  q.push({
    id: "adresse_bestaetigen",
    question: "Ich habe Ihre Adresse als {{street}} {{house_number}}, {{postal_code}} {{city}}. Ist das korrekt?",
    type: "boolean",
    required: true,
    priority: 1,
    group: "Kontakt",
    source: { verbatim: false }
  });

  // === PROTOCOL-BASED QUESTIONS (same as buildQuestions) ===
  
  return [...q, ...buildProtocolQuestions(extr)];
}

/**
 * Builds protocol-based questions (no applicant data needed).
 * These questions are the same for template and non-template mode.
 */
function buildProtocolQuestions(extr: ExtractResult): Question[] {
  const q: Question[] = [];

  // 1. Standort
  if (!extr.sites?.length) {
    q.push({
      id: "standort_erfragen",
      question: "An welchem Standort möchten Sie arbeiten?",
      type: "string",
      required: true,
      priority: 1,
      group: "Standort",
      source: { verbatim: false }
    });
  } else if (extr.sites.length === 1) {
    q.push({
      id: "standort_bestaetigung",
      question: `Unser Standort ist ${extr.sites[0].label}. Passt das für Sie?`,
      type: "boolean",
      required: true,
      priority: 1,
      group: "Standort",
      source: { verbatim: false }
    });
  } else {
    q.push({
      id: "standort_wahl",
      question: "An welchem unserer Standorte möchten Sie gerne arbeiten?",
      type: "choice",
      options: extr.sites.map(s => s.label),
      required: true,
      priority: 1,
      group: "Standort",
      source: { verbatim: false }
    });
  }

  // 2. Einsatzbereich (verbatim wenn vorhanden)
  const verbatimDept = (extr.verbatim_candidates || []).find(v =>
    v.is_real_question && /fachabteilung|bereich/i.test(v.text)
  );
  const deptText = verbatimDept
    ? verbatimDept.text.replace(/\(.*?\)/g, "").trim()
    : "In welcher Fachabteilung möchten Sie gerne arbeiten?";

  q.push({
    id: "bereich",
    question: deptText,
    type: "choice",
    options: extr.all_departments,
    required: true,
    priority: 1,
    group: "Einsatzbereich",
    source: {
      page_id: verbatimDept?.page_id,
      prompt_id: verbatimDept?.prompt_id,
      verbatim: Boolean(verbatimDept)
    },
    input_hint: "Bitte eine Abteilung nennen."
  });

  // 3. Muss-Kriterium Pflegeexamen
  if ((extr.must_have || []).some(m => /pflegefach/i.test(m))) {
    q.push({
      id: "examen_pflege",
      question: "Sind Sie examinierte Pflegefachfrau oder Pflegefachmann?",
      type: "boolean",
      required: true,
      priority: 1,
      group: "Qualifikation",
      source: { verbatim: false },
      context: "Muss-Kriterium aus Protokoll"
    });
  }

  // 4. Alternative OP/MFA
  if ((extr.alternatives || []).some(a => /MFA/i.test(a))) {
    q.push({
      id: "op_mfa_alternative",
      question: "Wären Sie alternativ für den OP-Bereich mit einer MFA-Qualifizierungsmaßnahme offen?",
      type: "boolean",
      required: false,
      priority: 2,
      group: "Qualifikation",
      source: { verbatim: false }
    });
  }

  // 5. Prioritäten → Präferenzfragen
  for (const prio of extr.priorities || []) {
    q.push({
      id: `prio_${slug(prio.label)}`,
      question: `Haben Sie besonderes Interesse am Bereich ${prio.label}?`,
      type: "boolean",
      required: false,
      priority: prio.prio_level || 2,
      group: "Präferenzen",
      help_text: prio.reason || "",
      source: {
        page_id: prio.source?.page_id,
        prompt_id: prio.source?.prompt_id,
        verbatim: false
      }
    });
  }

  // 6. Arbeitszeitmodell
  q.push({
    id: "arbeitszeitmodell",
    question: "Welches Arbeitszeitmodell bevorzugen Sie?",
    type: "choice",
    options: [
      extr.constraints?.arbeitszeit?.vollzeit
        ? `Vollzeit (${extr.constraints.arbeitszeit.vollzeit})`
        : "Vollzeit",
      extr.constraints?.arbeitszeit?.teilzeit
        ? `Teilzeit (${extr.constraints.arbeitszeit.teilzeit})`
        : "Teilzeit"
    ],
    required: true,
    priority: 2,
    group: "Rahmen",
    source: { verbatim: false }
  });

  // 7. Schichten
  if (extr.constraints?.schichten) {
    q.push({
      id: "schichten",
      question: "Welche Schichten können Sie abdecken?",
      type: "multi_choice",
      options: ["Früh", "Spät", "Nacht", "Wechsel", "individuelle Anpassungen möglich"],
      required: false,
      priority: 2,
      group: "Rahmen",
      help_text: extr.constraints.schichten,
      source: { verbatim: false }
    });
  }

  // 8. Tarif
  if (extr.constraints?.tarif) {
    q.push({
      id: "tarif_info",
      question: `Die Vergütung ist an den ${extr.constraints.tarif} angelehnt. Ist das für Sie grundsätzlich in Ordnung?`,
      type: "boolean",
      required: false,
      priority: 3,
      group: "Rahmen",
      source: { verbatim: false }
    });
  }
  
  return q;
}

/**
 * Builds questions with actual applicant data (original behavior).
 * This mode is for backward compatibility.
 */
export function buildQuestions(extr: ExtractResult, candidate: CandidateProfile): Question[] {
  const q: Question[] = [];

  // 1. Standort
  if (!extr.sites?.length) {
    q.push({
      id: "standort_erfragen",
      question: "An welchem Standort möchten Sie arbeiten?",
      type: "string",
      required: true,
      priority: 1,
      group: "Standort",
      source: { verbatim: false }
    });
  } else if (extr.sites.length === 1) {
    q.push({
      id: "standort_bestaetigung",
      question: `Unser Standort ist ${extr.sites[0].label}. Passt das für Sie?`,
      type: "boolean",
      required: true,
      priority: 1,
      group: "Standort",
      source: { verbatim: false }
    });
  } else {
    q.push({
      id: "standort_wahl",
      question: "An welchem unserer Standorte möchten Sie gerne arbeiten?",
      type: "choice",
      options: extr.sites.map(s => s.label),
      required: true,
      priority: 1,
      group: "Standort",
      source: { verbatim: false }
    });
  }

  // 2. Einsatzbereich (verbatim wenn vorhanden)
  const verbatimDept = (extr.verbatim_candidates || []).find(v =>
    v.is_real_question && /fachabteilung|bereich/i.test(v.text)
  );
  const deptText = verbatimDept
    ? verbatimDept.text.replace(/\(.*?\)/g, "").trim()
    : "In welcher Fachabteilung möchten Sie gerne arbeiten?";

  q.push({
    id: "bereich",
    question: deptText,
    type: "choice",
    options: extr.all_departments,
    required: true,
    priority: 1,
    group: "Einsatzbereich",
    source: {
      page_id: verbatimDept?.page_id,
      prompt_id: verbatimDept?.prompt_id,
      verbatim: Boolean(verbatimDept)
    },
    input_hint: "Bitte eine Abteilung nennen."
  });

  // 3. Muss-Kriterium Pflegeexamen
  if ((extr.must_have || []).some(m => /pflegefach/i.test(m))) {
    q.push({
      id: "examen_pflege",
      question: "Sind Sie examinierte Pflegefachfrau oder Pflegefachmann?",
      type: "boolean",
      required: true,
      priority: 1,
      group: "Qualifikation",
      source: { verbatim: false },
      context: "Muss-Kriterium aus Protokoll"
    });
  }

  // 4. Alternative OP/MFA (Bedingungen später in validate)
  if ((extr.alternatives || []).some(a => /MFA/i.test(a))) {
    q.push({
      id: "op_mfa_alternative",
      question: "Wären Sie alternativ für den OP-Bereich mit einer MFA-Qualifizierungsmaßnahme offen?",
      type: "boolean",
      required: false,
      priority: 2,
      group: "Qualifikation",
      source: { verbatim: false }
    });
  }

  // 5. Prioritäten → Präferenzfragen mit Begründung als help_text
  for (const prio of extr.priorities || []) {
    q.push({
      id: `prio_${slug(prio.label)}`,
      question: `Haben Sie besonderes Interesse am Bereich ${prio.label}?`,
      type: "boolean",
      required: false,
      priority: prio.prio_level || 2,
      group: "Präferenzen",
      help_text: prio.reason,
      source: {
        page_id: prio.source?.page_id,
        prompt_id: prio.source?.prompt_id,
        verbatim: false
      }
    });
  }

  // 6. Rahmenbedingungen: Arbeitszeit
  q.push({
    id: "arbeitszeitmodell",
    question: "Welches Arbeitszeitmodell bevorzugen Sie?",
    type: "choice",
    options: [
      extr.constraints?.arbeitszeit?.vollzeit
        ? `Vollzeit (${extr.constraints.arbeitszeit.vollzeit})`
        : "Vollzeit",
      extr.constraints?.arbeitszeit?.teilzeit
        ? `Teilzeit (${extr.constraints.arbeitszeit.teilzeit})`
        : "Teilzeit"
    ],
    required: true,
    priority: 2,
    group: "Rahmen",
    source: { verbatim: false }
  });

  // 7. Schichten
  if (extr.constraints?.schichten) {
    q.push({
      id: "schichten",
      question: "Welche Schichten können Sie abdecken?",
      type: "multi_choice",
      options: ["Früh", "Spät", "Nacht", "Wechsel", "individuelle Anpassungen möglich"],
      required: false,
      priority: 2,
      group: "Rahmen",
      help_text: extr.constraints.schichten,
      source: { verbatim: false }
    });
  }

  // 8. Tarif
  if (extr.constraints?.tarif) {
    q.push({
      id: "tarif_info",
      question: `Die Vergütung ist an den ${extr.constraints.tarif} angelehnt. Ist das für Sie grundsätzlich in Ordnung?`,
      type: "boolean",
      required: false,
      priority: 3,
      group: "Rahmen",
      source: { verbatim: false }
    });
  }

  // 9. Adresse: Prefill vs. Erfassen
  if (candidate.address_full) {
    q.push({
      id: "adresse_bestaetigen",
      question: `Ich habe Ihre Adresse als ${candidate.address_full}. Ist das korrekt?`,
      type: "boolean",
      required: true,
      priority: 1,
      group: "Kontakt",
      source: { verbatim: false }
    });
  } else {
    q.push({
      id: "adresse",
      question: "Wie lautet Ihre genaue Adresse (Straße, Hausnummer, PLZ und Ort)?",
      type: "string",
      required: true,
      priority: 1,
      group: "Kontakt",
      source: { verbatim: true }
    });
  }

  return q;
}

