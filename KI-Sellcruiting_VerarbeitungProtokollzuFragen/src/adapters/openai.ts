import OpenAI from "openai";
import { retry } from "@lifeomic/attempt";
import { logger } from "../utils/log";

export const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY!
});

export async function callResponses(input: any) {
  const started = Date.now();

  const res = await retry(
    async () => {
      const r = await openai.chat.completions.create(input);
      const text = r.choices[0]?.message?.content?.trim();
      if (!text) throw new Error("Empty output from LLM");
      (r as any).__duration_ms = Date.now() - started;
      return r;
    },
    {
      maxAttempts: 3,
      delay: 1000,
      factor: 2,
      handleError(err: any, ctx) {
        if (err.status === 400) ctx.abort();
        logger.warn(
          { attempt: ctx.attemptNum, error: String(err) },
          "Retrying OpenAI call"
        );
      }
    }
  );

  const tokens = res.usage?.total_tokens || 0;
  const cost_usd = (tokens * 0.00001).toFixed(4);

  logger.info(
    {
      model: input.model,
      duration_ms: (res as any).__duration_ms,
      tokens,
      cost_usd
    },
    "OpenAI call done"
  );

  return res;
}

