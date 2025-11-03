import fs from "node:fs/promises";
import Ajv from "ajv";
import addFormats from "ajv-formats";
import { callResponses } from "../adapters/openai";
import { EXTRACT_SCHEMA } from "../schema/extract.schema";
import { logger } from "../utils/log";
import type { ExtractResult } from "../types";

const ajv = new Ajv({ allErrors: true });
addFormats(ajv);
const validateExtract = ajv.compile(EXTRACT_SCHEMA);

export async function extract(protocol: any): Promise<ExtractResult> {
  const system = await fs.readFile("src/prompts/extract.system.md", "utf8");

  const model = process.env.OPENAI_MODEL || "gpt-5";
  
  // GPT-5 unterstützt nur temperature: 1 (Standard)
  // Andere Modelle können 0.2 nutzen
  const temperature = model === "gpt-5" ? 1 : 0.2;

  const res = await callResponses({
    model: model,  // ✅ Nutzt GPT-5 (neuestes Modell seit Aug 2025)
    temperature: temperature,
    messages: [
      { role: "system", content: system },
      { role: "user", content: JSON.stringify({ protocol }) }
    ],
    response_format: { type: "json_object" }
  });

  const content = res.choices[0]?.message?.content;
  if (!content) {
    throw new Error("LLM returned no content");
  }

  const json = JSON.parse(content);

  if (!validateExtract(json)) {
    logger.error({ errors: validateExtract.errors }, "LLM Extract invalid");
    throw new Error("LLM Extract invalid: " + JSON.stringify(validateExtract.errors));
  }

  // Nach-Normalisierung: Dedupe + Sort
  json.all_departments = Array.from(new Set(json.all_departments || [])).sort();

  logger.info(
    {
      sites_found: json.sites?.length || 0,
      priorities_found: json.priorities?.length || 0,
      departments_found: json.all_departments?.length || 0
    },
    "Extract complete"
  );

  return json as ExtractResult;
}

