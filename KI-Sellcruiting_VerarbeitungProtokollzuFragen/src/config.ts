export const config = {
  openai: {
    model: process.env.OPENAI_MODEL || "gpt-4.1-mini",
    temperature: 0.2,
    maxRetries: 3,
    retryDelayMs: 1000
  },
  catalog: {
    maxQuestions: 20,
    defaultPriority: 2
  },
  rules: {
    singleSiteSkipsChoice: true,
    dedupeStations: true,
    normalizeNumbers: true
  }
};

