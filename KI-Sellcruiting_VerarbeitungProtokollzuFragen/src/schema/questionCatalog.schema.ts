export const QUESTION_CATALOG_SCHEMA = {
  type: "object",
  required: ["_meta", "questions"],
  properties: {
    _meta: {
      type: "object",
      required: ["schema_version", "generated_at", "generator"],
      properties: {
        schema_version: { type: "string" },
        generated_at: { type: "string" },
        generator: { type: "string" }
      }
    },
    questions: {
      type: "array",
      items: {
        type: "object",
        required: ["id", "question", "type", "required", "priority"],
        properties: {
          id: { type: "string" },
          question: { type: "string" },
          type: {
            enum: ["string", "date", "boolean", "choice", "multi_choice", "ranked_list"]
          },
          options: { type: "array", items: { type: "string" } },
          conversation_flow: {
            type: "object",
            properties: {
              pre_check: {
                type: "object",
                required: ["question", "on_yes", "on_no"],
                properties: {
                  question: { type: "string" },
                  on_yes: { type: "string" },
                  on_no: { type: "string" }
                },
                additionalProperties: false
              },
              open_question: {
                type: "object",
                required: ["question", "allow_fuzzy_match", "on_unclear"],
                properties: {
                  question: { type: "string" },
                  allow_fuzzy_match: { type: "boolean" },
                  on_unclear: { type: "string" }
                },
                additionalProperties: false
              },
              clustered_options: {
                type: "object",
                required: ["presentation_hint", "categories"],
                properties: {
                  presentation_hint: { type: "string" },
                  categories: {
                    type: "array",
                    items: {
                      type: "object",
                      required: ["id", "label", "options"],
                      properties: {
                        id: { type: "string" },
                        label: { type: "string" },
                        options: { type: "array", items: { type: "string" } }
                      },
                      additionalProperties: false
                    }
                  }
                },
                additionalProperties: false
              }
            },
            additionalProperties: false
          },
          required: { type: "boolean" },
          priority: { enum: [1, 2, 3] },
          group: { type: "string" },
          help_text: { type: "string" },
          input_hint: { type: "string" },
          conditions: {
            type: "array",
            items: {
              type: "object",
              required: ["when", "then"],
              properties: {
                when: {
                  type: "object",
                  required: ["field", "op"],
                  properties: {
                    field: { type: "string" },
                    op: { enum: ["eq", "in", "exists"] },
                    value: {}
                  }
                },
                then: {
                  type: "object",
                  required: ["action"],
                  properties: {
                    action: { enum: ["ask", "skip", "prefill", "reorder"] },
                    value: {}
                  }
                }
              },
              additionalProperties: false
            }
          },
          source: {
            type: "object",
            properties: {
              page_id: { type: "integer" },
              prompt_id: { type: "integer" },
              verbatim: { type: "boolean" }
            },
            additionalProperties: false
          },
          context: { type: "string" },
          category: { type: "string" },
          category_order: { type: "integer" }
        },
        additionalProperties: false
      }
    }
  }
} as const;

