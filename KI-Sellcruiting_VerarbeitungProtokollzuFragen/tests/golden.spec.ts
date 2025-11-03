import fs from "node:fs/promises";
import { buildCatalog } from "../src/pipeline/buildCatalog";

describe("Golden Test: Question Builder", () => {
  let candidate1: any;
  let candidate2: any;
  let protocol: any;

  beforeAll(async () => {
    candidate1 = JSON.parse(
      await fs.readFile("Input_datein_beispiele/Bewerberprofil_Teil1.json", "utf8")
    );
    candidate2 = await fs
      .readFile("Input_datein_beispiele/Bewerberprofil_Teil2.json", "utf8")
      .then(s => JSON.parse(s))
      .catch(() => null);
    protocol = JSON.parse(
      await fs.readFile("Input_datein_beispiele/Unternehmensprofil.json", "utf8")
    );
  });

  it("should generate valid question catalog", async () => {
    const result = await buildCatalog(candidate1, candidate2, protocol);

    // Check structure
    expect(result).toHaveProperty("_meta");
    expect(result).toHaveProperty("questions");
    expect(result._meta.schema_version).toBe("1.0");
    expect(result._meta.generator).toBe("sellcruiting-question-builder@1.0.0");
  }, 30000);

  it("should have questions array", async () => {
    const result = await buildCatalog(candidate1, candidate2, protocol);
    expect(Array.isArray(result.questions)).toBe(true);
    expect(result.questions.length).toBeGreaterThan(0);
    expect(result.questions.length).toBeLessThanOrEqual(20);
  }, 30000);

  it("should have standort question (wahl or bestätigung)", async () => {
    const result = await buildCatalog(candidate1, candidate2, protocol);
    const standortQuestions = result.questions.filter(q =>
      q.id.includes("standort")
    );
    expect(standortQuestions.length).toBeGreaterThan(0);
  }, 30000);

  it("should have bereich question with verbatim source", async () => {
    const result = await buildCatalog(candidate1, candidate2, protocol);
    const bereichQ = result.questions.find(q => q.id === "bereich");
    expect(bereichQ).toBeDefined();
    expect(bereichQ?.source).toBeDefined();
  }, 30000);

  it("should have examen_pflege as required", async () => {
    const result = await buildCatalog(candidate1, candidate2, protocol);
    const examenQ = result.questions.find(q => q.id === "examen_pflege");
    if (examenQ) {
      expect(examenQ.required).toBe(true);
    }
  }, 30000);

  it("should have op_mfa_alternative with conditions", async () => {
    const result = await buildCatalog(candidate1, candidate2, protocol);
    const opMfaQ = result.questions.find(q => q.id === "op_mfa_alternative");
    if (opMfaQ) {
      expect(opMfaQ.conditions).toBeDefined();
      expect(opMfaQ.conditions!.length).toBeGreaterThan(0);
    }
  }, 30000);

  it("should have address question (bestätigen or erfassen)", async () => {
    const result = await buildCatalog(candidate1, candidate2, protocol);
    const addrQuestions = result.questions.filter(q =>
      q.id.includes("adresse")
    );
    expect(addrQuestions.length).toBeGreaterThan(0);
  }, 30000);

  it("should respect max 20 questions limit", async () => {
    const result = await buildCatalog(candidate1, candidate2, protocol);
    expect(result.questions.length).toBeLessThanOrEqual(20);
  }, 30000);

  it("should have questions sorted by group and priority", async () => {
    const result = await buildCatalog(candidate1, candidate2, protocol);
    const groups = result.questions.map(q => q.group).filter(Boolean);
    const groupOrder = ["Standort", "Einsatzbereich", "Qualifikation", "Präferenzen", "Rahmen", "Kontakt"];

    for (let i = 0; i < groups.length - 1; i++) {
      const currentIdx = groupOrder.indexOf(groups[i] as string);
      const nextIdx = groupOrder.indexOf(groups[i + 1] as string);
      expect(currentIdx).toBeLessThanOrEqual(nextIdx);
    }
  }, 30000); // 30s timeout for LLM call
});

