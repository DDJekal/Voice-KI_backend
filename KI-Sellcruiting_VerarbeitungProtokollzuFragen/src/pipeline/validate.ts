import type { Question } from "../types";
import { Rules } from "../rules";

export function validateAndFinalize(base: Question[], ctx: any): Question[] {
  let q = base;

  // Regeln in Reihenfolge anwenden
  q = Rules.singleSite(ctx, q);
  q = Rules.zeroSiteFallback(ctx, q);
  q = Rules.opMfaConditional(ctx, q);
  q = Rules.prioritiesBoost(ctx, q);
  q = Rules.singleOptionToBoolean(ctx, q);  // Choice mit 1 Option → boolean
  q = Rules.dedupeAndSortLimit(ctx, q);

  return q;
}

