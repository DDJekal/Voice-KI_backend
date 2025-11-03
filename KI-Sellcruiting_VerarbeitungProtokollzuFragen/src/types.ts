export interface CandidateProfile {
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  telephone: string | null;
  birthday: string | null;
  salutation: number | null;
  is_in_internal_review?: boolean;
  is_qualified?: boolean;
  is_rejected?: boolean;
  is_hired?: boolean;
  information?: string;
  // Extended with merged address
  address_full?: string | null;
}

export interface ConversationProtocol {
  id: number;
  name: string;
  pages: Page[];
  created_on?: string;
  updated_on?: string;
}

export interface Page {
  id: number;
  name: string;
  position: number;
  prompts: Prompt[];
  created_on?: string;
  updated_on?: string;
}

export interface Prompt {
  id: number;
  position: number;
  question: string;
  checked?: any;
  information?: any;
  is_template?: boolean;
  created_on?: string;
  updated_on?: string;
}

export interface ExtractResult {
  sites: Array<{
    label: string;
    stations: string[];
    source?: { page_id: number };
  }>;
  roles: string[];
  priorities: Array<{
    label: string;
    reason: string;
    prio_level: 1 | 2 | 3;
    source?: { page_id: number; prompt_id?: number };
  }>;
  must_have: string[];
  alternatives: string[];
  constraints: {
    arbeitszeit?: {
      vollzeit?: string;
      teilzeit?: string;
    };
    tarif?: string;
    schichten?: string;
  };
  verbatim_candidates: Array<{
    text: string;
    page_id: number;
    prompt_id?: number;
    is_real_question: boolean;
  }>;
  all_departments: string[];
}

export type QuestionType = "string" | "date" | "boolean" | "choice" | "multi_choice" | "ranked_list";

export interface Question {
  id: string;
  question: string;
  type: QuestionType;
  options?: string[];
  
  // Conversation Flow für voice-optimierte Fragen mit vielen Optionen
  conversation_flow?: {
    pre_check: {
      question: string;
      on_yes: "open_question";
      on_no: "clustered_options";
    };
    open_question: {
      question: string;
      allow_fuzzy_match: boolean;
      on_unclear: "clustered_options";
    };
    clustered_options: {
      presentation_hint: string;
      categories: Array<{
        id: string;
        label: string;
        options: string[];
      }>;
    };
  };
  
  required: boolean;
  priority: 1 | 2 | 3;
  group?: "Standort" | "Einsatzbereich" | "Qualifikation" | "Präferenzen" | "Rahmen" | "Kontakt";
  help_text?: string;
  input_hint?: string;
  conditions?: Array<{
    when: {
      field: string;
      op: "eq" | "in" | "exists";
      value?: any;
    };
    then: {
      action: "ask" | "skip" | "prefill" | "reorder";
      value?: any;
    };
  }>;
  source?: {
    page_id?: number;
    prompt_id?: number;
    verbatim?: boolean;
  };
  context?: string;
}

export interface QuestionCatalog {
  _meta: {
    schema_version: string;
    generated_at: string;
    generator: string;
  };
  questions: Question[];
}

