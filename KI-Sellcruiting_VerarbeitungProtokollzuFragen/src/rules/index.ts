import type { Question } from "../types";

export const Rules = {
  /**
   * Entfernt Standort-Auswahl bei nur 1 Standort
   */
  singleSite: (ctx: any, q: Question[]): Question[] => {
    if ((ctx.sites?.length || 0) === 1) {
      return q.filter(x => x.id !== "standort_wahl");
    }
    return q;
  },

  /**
   * Fallback für 0 Standorte (standort_erfragen wurde schon erzeugt)
   */
  zeroSiteFallback: (ctx: any, q: Question[]): Question[] => {
    // Nichts zu tun, standort_erfragen wird bereits in structure.ts erzeugt
    return q;
  },

  /**
   * Setzt Bedingung für OP/MFA-Frage
   */
  opMfaConditional: (_ctx: any, q: Question[]): Question[] => {
    const target = q.find(x => x.id === "op_mfa_alternative");
    if (target) {
      target.conditions = [
        {
          when: {
            field: "bereich",
            op: "in",
            value: ["OP", "Anästhesie", "Endoskopie"]
          },
          then: { action: "ask" }
        }
      ];
    }
    return q;
  },

  /**
   * Hebt Priority basierend auf Extract-Prioritäten
   */
  prioritiesBoost: (ctx: any, q: Question[]): Question[] => {
    for (const prio of ctx.priorities || []) {
      const item = q.find(x => x.id === `prio_${prio.slug}`);
      if (item) {
        item.priority = Math.min(item.priority ?? 2, prio.prio_level ?? 2) as 1 | 2 | 3;
      }
    }
    return q;
  },

  /**
   * Wandelt choice-Fragen mit nur 1 Option in boolean um
   */
  singleOptionToBoolean: (_ctx: any, q: Question[]): Question[] => {
    return q.map(item => {
      // Nur choice-Fragen mit genau 1 Option
      if (item.type === "choice" && item.options?.length === 1) {
        const option = item.options[0];
        return {
          ...item,
          type: "boolean" as const,
          question: `Möchten Sie im Bereich ${option} arbeiten?`,
          options: undefined // boolean braucht keine options
        };
      }
      return item;
    });
  },

  /**
   * Dedupliziert, sortiert und limitiert auf 20 Fragen
   */
  dedupeAndSortLimit: (_ctx: any, q: Question[]): Question[] => {
    const seen = new Set<string>();
    const out: Question[] = [];

    for (const item of q) {
      const sig = `${item.id}:${item.question}`;
      if (!seen.has(sig)) {
        seen.add(sig);
        out.push(item);
      }
    }

    // Sortierung: group → priority → id (mit Conversational Flow Logik)
    const groupOrder = ["Standort", "Einsatzbereich", "Qualifikation", "Präferenzen", "Rahmen", "Kontakt"];
    
    // Hilfsfunktion: Gibt Sortier-Wert für Conversational Flow IDs
    const getFlowOrder = (id: string): number => {
      if (id.endsWith("_pre_check")) return 0; // Zuerst
      if (id.endsWith("_open")) return 1;      // Zweites
      return 2;                                 // Basis-Frage zuletzt
    };
    
    // Hilfsfunktion: Extrahiert Basis-ID (ohne _pre_check/_open Suffix)
    const getBaseId = (id: string): string => {
      return id.replace(/_pre_check$|_open$/, "");
    };
    
    out.sort((a, b) => {
      const groupA = groupOrder.indexOf(a.group || "Z");
      const groupB = groupOrder.indexOf(b.group || "Z");
      if (groupA !== groupB) return groupA - groupB;
      if (a.priority !== b.priority) return a.priority - b.priority;
      
      // Wenn gleiche Basis-ID (z.B. "bereich"), nach Flow-Order sortieren
      const baseA = getBaseId(a.id);
      const baseB = getBaseId(b.id);
      if (baseA === baseB) {
        return getFlowOrder(a.id) - getFlowOrder(b.id);
      }
      
      // Sonst alphabetisch
      return a.id.localeCompare(b.id);
    });

    // Limitierung auf 20
    return out.slice(0, 20);
  }
};

