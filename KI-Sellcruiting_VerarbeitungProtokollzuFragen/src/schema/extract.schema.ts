export const EXTRACT_SCHEMA = {
  type: "object",
  required: ["sites", "priorities", "must_have", "all_departments"],
  properties: {
    sites: {
      type: "array",
      items: {
        type: "object",
        required: ["label", "stations"],
        properties: {
          label: { type: "string" },
          stations: { type: "array", items: { type: "string" } },
          source: {
            type: "object",
            properties: { page_id: { type: "integer" } },
            additionalProperties: true
          }
        }
      }
    },
    roles: {
      type: "array",
      items: { type: "string" }
    },
    priorities: {
      type: "array",
      items: {
        type: "object",
        required: ["label", "reason"],
        properties: {
          label: { type: "string" },
          reason: { type: "string" },
          prio_level: { enum: [1, 2, 3], default: 2 },
          source: {
            type: "object",
            properties: {
              page_id: { type: "integer" },
              prompt_id: { type: "integer" }
            },
            additionalProperties: true
          }
        }
      }
    },
    must_have: { type: "array", items: { type: "string" } },
    alternatives: { type: "array", items: { type: "string" } },
    constraints: {
      type: "object",
      properties: {
        arbeitszeit: {
          type: "object",
          properties: {
            vollzeit: { type: "string" },
            teilzeit: { type: "string" }
          }
        },
        tarif: { type: "string" },
        schichten: { type: "string" }
      }
    },
    verbatim_candidates: {
      type: "array",
      items: {
        type: "object",
        required: ["text", "page_id"],
        properties: {
          text: { type: "string" },
          page_id: { type: "integer" },
          prompt_id: { type: "integer" },
          is_real_question: { type: "boolean", default: false }
        },
        additionalProperties: true
      }
    },
    all_departments: { type: "array", items: { type: "string" } }
  },
  additionalProperties: true
} as const;

