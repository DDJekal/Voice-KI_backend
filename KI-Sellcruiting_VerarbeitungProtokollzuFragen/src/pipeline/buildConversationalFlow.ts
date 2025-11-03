import fs from "node:fs/promises";
import { callResponses } from "../adapters/openai";
import { logger } from "../utils/log";
import type { Question } from "../types";

interface FlowContext {
  priorities?: Array<{ label: string; reason: string }>;
}

/**
 * Konvertiert choice-Fragen mit vielen Optionen in conversational flows
 */
export async function buildConversationalFlow(
  questions: Question[],
  context: FlowContext
): Promise<Question[]> {
  const THRESHOLD = 7;
  
  // Finde choice-Fragen mit vielen Optionen ODER Standort-Wahl mit >= 2 Optionen
  const candidateQuestions = questions.filter(
    q => q.type === "choice" && q.options && (
      q.options.length > THRESHOLD ||
      (q.id === "standort_wahl" && q.options.length >= 2)
    )
  );
  
  if (candidateQuestions.length === 0) {
    logger.info("No questions need conversational flow");
    return questions;
  }
  
  logger.info(
    { count: candidateQuestions.length, threshold: THRESHOLD },
    "Building conversational flows"
  );
  
  // Bereite Input für LLM vor
  const input = {
    questions: candidateQuestions.map(q => ({
      id: q.id,
      question: q.question,
      options: q.options,
      group: q.group,
      priority_hints: context.priorities?.filter(p => 
        q.options?.some(opt => 
          opt.toLowerCase().includes(p.label.toLowerCase()) ||
          p.label.toLowerCase().includes(opt.toLowerCase())
        )
      )
    })),
    context: {
      priorities: context.priorities
    }
  };
  
  try {
    const system = await fs.readFile("src/prompts/conversational-flow.system.md", "utf8");
    
    const res = await callResponses({
      model: process.env.OPENAI_MODEL || "gpt-4o-mini",
      temperature: 0.3,
      messages: [
        { role: "system", content: system },
        { role: "user", content: JSON.stringify(input) }
      ],
      response_format: { type: "json_object" }
    });
    
    const content = res.choices[0]?.message?.content;
    if (!content) {
      logger.warn("LLM returned no flows, using original questions");
      return questions;
    }
    
    const flows = JSON.parse(content);
    
    // Debug: Log LLM response
    logger.debug({ flows }, "LLM conversational flow response");
    
    // Normalisiere Response-Format: handle both single object and array
    const flowArray = flows.conversational_flows 
      ? flows.conversational_flows 
      : (flows.question_id ? [flows] : []);
    
    logger.debug({ flowCount: flowArray.length }, "Normalized flows");
    
    // Merge zurück in Questions
    const result = questions.map(q => {
      const flow = flowArray.find((f: any) => f.question_id === q.id);
      
      if (flow) {
        logger.debug(
          { 
            question_id: q.id,
            has_pre_check: !!flow.pre_check,
            has_open_question: !!flow.open_question,
            has_clustered_options: !!flow.clustered_options,
            flow
          },
          "Flow validation"
        );
      }
      
      if (flow && flow.pre_check && flow.open_question && flow.clustered_options) {
        return {
          ...q,
          conversation_flow: {
            pre_check: flow.pre_check,
            open_question: flow.open_question,
            clustered_options: flow.clustered_options
          }
        };
      }
      
      return q;
    });
    
    logger.info(
      { 
        converted: result.filter(q => q.conversation_flow).length,
        total: result.length 
      },
      "Conversational flows built"
    );
    
    return result;
    
  } catch (error) {
    logger.error({ error: String(error) }, "Failed to build conversational flows");
    logger.warn("Falling back to original questions");
    return questions;
  }
}

