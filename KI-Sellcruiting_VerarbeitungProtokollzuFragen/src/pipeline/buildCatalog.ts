import Ajv from "ajv";
import addFormats from "ajv-formats";
import { cleanProtocol, mergeCandidate } from "../utils/preprocess";
import { extract } from "./extract";
import { buildQuestions, buildQuestionsTemplate } from "./structure";
import { buildConversationalFlow } from "./buildConversationalFlow";
import { expandConversationalFlow } from "./expandConversationalFlow";
import { validateAndFinalize } from "./validate";
import { categorizeQuestion } from "../categorization/categorizer";
import { QUESTION_CATALOG_SCHEMA } from "../schema/questionCatalog.schema";
import { logger } from "../utils/log";
import { slug } from "../utils/text";
import type { QuestionCatalog } from "../types";

const ajv = new Ajv({ allErrors: true });
addFormats(ajv);
const validateCatalog = ajv.compile(QUESTION_CATALOG_SCHEMA);

export async function buildCatalog(
  candidatePart1: any,
  candidatePart2: any | null,
  protocol: any
): Promise<QuestionCatalog> {
  // 1. Pre-Processing
  const candidate = mergeCandidate(candidatePart1, candidatePart2 || undefined);
  const normalizedProtocol = cleanProtocol(protocol);

  // 2. Extract (LLM-Call)
  const extr = await extract(normalizedProtocol);

  // 3. Structure (deterministisch)
  const base = buildQuestions(extr, candidate);

  // 4. Build Conversational Flows (LLM-Call)
  const conversational = await buildConversationalFlow(base, {
    priorities: extr.priorities
  });

  // 5. Expand Conversational Flows (in separate Fragen aufteilen)
  const expanded = expandConversationalFlow(conversational);

  // 6. Validate (Regeln anwenden)
  const ctx = {
    sites: extr.sites,
    priorities: (extr.priorities || []).map((p: any) => ({
      ...p,
      slug: slug(p.label)
    })),
    candidate: { address_full: candidate.address_full }
  };
  const final = validateAndFinalize(expanded, ctx);

  // 6.5. Kategorisierung hinzufügen
  const categorized = final.map(q => {
    // Versuche aus Kontext zu kategorisieren
    // Da wir hier keine Page-Infos haben, nutzen wir die Frage selbst
    const mockPage = { name: q.group || '' };
    const mockPrompt = { 
      question: q.question, 
      type: q.type === 'boolean' ? 'yes_no' : 'text'
    };
    
    const catMapping = categorizeQuestion(mockPrompt, mockPage);
    
    return {
      ...q,
      category: catMapping.category,
      category_order: catMapping.order
    };
  });

  // 7. Wrap mit _meta
  const wrapped: QuestionCatalog = {
    _meta: {
      schema_version: "1.0",
      generated_at: new Date().toISOString(),
      generator: "sellcruiting-question-builder@1.0.0"
    },
    questions: categorized
  };

  // 8. Ajv-Validierung
  if (!validateCatalog(wrapped)) {
    logger.error({ errors: validateCatalog.errors }, "Final catalog invalid");
    throw new Error("Final catalog invalid: " + JSON.stringify(validateCatalog.errors, null, 2));
  }

  logger.info(
    {
      total_questions: wrapped.questions.length,
      conversational_questions: wrapped.questions.filter(q => q.conversation_flow).length,
      groups: [...new Set(wrapped.questions.map(q => q.group))].filter(Boolean)
    },
    "Catalog built successfully"
  );

  return wrapped;
}

/**
 * Builds a catalog with {{variable}} templates (no applicant data).
 * This is used for generating campaign templates that can be reused.
 */
export async function buildCatalogTemplate(
  protocol: any
): Promise<QuestionCatalog> {
  // 1. Pre-Processing (no candidate data)
  const normalizedProtocol = cleanProtocol(protocol);

  // 2. Extract (LLM-Call)
  const extr = await extract(normalizedProtocol);

  // 3. Structure with Templates (no candidate needed)
  const base = buildQuestionsTemplate(extr);

  // 4. Build Conversational Flows (LLM-Call) - only if needed
  const conversational = await buildConversationalFlow(base, {
    priorities: extr.priorities
  });

  // 5. Expand Conversational Flows
  const expanded = expandConversationalFlow(conversational);

  // 6. Validate (minimal context - no candidate address)
  const ctx = {
    sites: extr.sites,
    priorities: (extr.priorities || []).map((p: any) => ({
      ...p,
      slug: slug(p.label)
    })),
    candidate: { address_full: null } // No candidate data in template mode
  };
  const final = validateAndFinalize(expanded, ctx);

  // 6.5. Kategorisierung hinzufügen
  const categorized = final.map(q => {
    const mockPage = { name: q.group || '' };
    const mockPrompt = { 
      question: q.question, 
      type: q.type === 'boolean' ? 'yes_no' : 'text'
    };
    
    const catMapping = categorizeQuestion(mockPrompt, mockPage);
    
    return {
      ...q,
      category: catMapping.category,
      category_order: catMapping.order
    };
  });

  // 7. Wrap mit _meta
  const wrapped: QuestionCatalog = {
    _meta: {
      schema_version: "1.0",
      generated_at: new Date().toISOString(),
      generator: "sellcruiting-question-builder@1.0.0-template"
    },
    questions: categorized
  };

  // 8. Ajv-Validierung
  if (!validateCatalog(wrapped)) {
    logger.error({ errors: validateCatalog.errors }, "Final template catalog invalid");
    throw new Error("Final template catalog invalid: " + JSON.stringify(validateCatalog.errors, null, 2));
  }

  logger.info(
    {
      total_questions: wrapped.questions.length,
      conversational_questions: wrapped.questions.filter(q => q.conversation_flow).length,
      template_variables: [...new Set(
        wrapped.questions.flatMap(q => 
          (q.question.match(/\{\{(\w+)\}\}/g) || [])
        )
      )],
      groups: [...new Set(wrapped.questions.map(q => q.group))].filter(Boolean)
    },
    "Template catalog built successfully"
  );

  return wrapped;
}

