import type { ConversationProtocol } from "../types";

export function mergeCandidate(part1: any, part2?: any) {
  const addr = part2
    ? `${part2.street ?? ""} ${part2.house_number ?? ""}, ${part2.postal_code ?? ""} ${part2.city ?? ""}`
        .replace(/\s+,/g, ",")
        .replace(/\s{2,}/g, " ")
        .trim()
    : null;

  return {
    ...part1,
    address_full: addr && addr.length > 5 ? addr : null
  };
}

export function cleanProtocol(protocol: ConversationProtocol): ConversationProtocol {
  if (!protocol?.pages?.length) {
    throw new Error("Protocol hat keine Seiten");
  }

  const strip = (s: string) =>
    s
      .replace(/^\s*\d+[\.\)]\s*/, "")  // "18. " entfernen
      .replace(/^\n+/, "")              // Leading newlines
      .trim();

  return {
    ...protocol,
    pages: protocol.pages.map(p => ({
      ...p,
      prompts: (p.prompts || [])
        .map(pr => ({ ...pr, question: strip(pr.question || "") }))
        .filter(pr => pr.question.length > 0)
    }))
  };
}

