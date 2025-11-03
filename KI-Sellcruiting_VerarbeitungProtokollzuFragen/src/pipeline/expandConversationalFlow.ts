import type { Question } from "../types";
import { logger } from "../utils/log";

/**
 * Expandiert Fragen mit conversation_flow in separate Fragen:
 * 1. Pre-Check (boolean)
 * 2. Open Question (string, conditional auf pre_check=yes)
 * 3. Choice mit Kategorien (conditional auf pre_check=no ODER open unclear)
 */
export function expandConversationalFlow(questions: Question[]): Question[] {
  const expanded: Question[] = [];
  
  for (const q of questions) {
    // Fragen ohne conversation_flow bleiben unverändert
    if (!q.conversation_flow) {
      expanded.push(q);
      continue;
    }
    
    const flow = q.conversation_flow;
    const baseId = q.id;
    
    // WICHTIG: Reihenfolge ist entscheidend - Pre-Check zuerst!
    
    // 1. Pre-Check Frage (geschlossen/boolean) - ZUERST
    expanded.push({
      id: `${baseId}_pre_check`,
      question: flow.pre_check.question,
      type: "boolean",
      required: q.required,
      priority: q.priority,
      group: q.group,
      source: q.source,
      help_text: "Diese Frage hilft uns, den Dialog effizienter zu gestalten"
    });
    
    // 2. Open Question (offen/string) - conditional auf JA
    expanded.push({
      id: `${baseId}_open`,
      question: flow.open_question.question,
      type: "string",
      required: false, // Nicht required, da conditional
      priority: q.priority,
      group: q.group,
      source: q.source,
      input_hint: q.input_hint,
      conditions: [
        {
          when: {
            field: `${baseId}_pre_check`,
            op: "eq",
            value: true
          },
          then: {
            action: "ask"
          }
        }
      ],
      context: flow.open_question.allow_fuzzy_match 
        ? "Fuzzy-Matching erlaubt - auch ähnliche Begriffe akzeptieren"
        : undefined
    });
    
    // 3. Choice mit Kategorien - conditional auf NEIN oder unclear - ZULETZT
    expanded.push({
      id: baseId, // Behält die Original-ID für Referenzen
      question: flow.clustered_options.presentation_hint,
      type: "choice",
      options: q.options, // Original-Optionen bleiben für Validierung
      required: false, // Nicht required, da conditional
      priority: q.priority,
      group: q.group,
      source: q.source,
      input_hint: q.input_hint,
      conditions: [
        {
          when: {
            field: `${baseId}_pre_check`,
            op: "eq",
            value: false
          },
          then: {
            action: "ask"
          }
        },
        {
          when: {
            field: `${baseId}_open`,
            op: "exists"
          },
          then: {
            action: "skip" // Wenn open beantwortet wurde, diese überspringen
          }
        }
      ],
      // Behalte clustered_options für Frontend-Rendering
      conversation_flow: {
        pre_check: flow.pre_check,
        open_question: flow.open_question,
        clustered_options: flow.clustered_options
      }
    });
    
    // Hinweis: Die 3 Fragen wurden in der richtigen Reihenfolge eingefügt:
    // 1. bereich_pre_check (boolean)
    // 2. bereich_open (string, conditional)
    // 3. bereich (choice, conditional)
  }
  
  logger.info(
    {
      original: questions.length,
      expanded: expanded.length,
      conversational: questions.filter(q => q.conversation_flow).length
    },
    "Conversational flows expanded into separate questions"
  );
  
  return expanded;
}

