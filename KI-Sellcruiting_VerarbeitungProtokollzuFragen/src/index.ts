import "dotenv/config";
import fs from "node:fs/promises";
import { buildCatalog, buildCatalogTemplate } from "./pipeline/buildCatalog";
import { logger } from "./utils/log";

async function main() {
  try {
    // Check for --template flag
    const isTemplateMode = process.argv.includes("--template");
    
    // CLI-Argument für Input-Ordner (default: Input_datein_beispiele)
    const inputDirArg = process.argv.find(arg => !arg.startsWith("--") && arg !== process.argv[0] && arg !== process.argv[1]);
    const inputDir = inputDirArg || "Input_datein_beispiele";
    
    logger.info(`Starting Question Builder... (Input: ${inputDir}, Template Mode: ${isTemplateMode})`);

    if (isTemplateMode) {
      // ===== TEMPLATE MODE: No applicant data needed =====
      logger.info("Template Mode: Loading protocol only (no applicant data)");
      
      // Suche nach Gesprächsprotokoll
      let protocol: any;
      try {
        protocol = JSON.parse(
          await fs.readFile(`${inputDir}/Gesprächsprotokoll_Beispiel2.json`, "utf8")
        );
      } catch {
        try {
          protocol = JSON.parse(
            await fs.readFile(`${inputDir}/Gesprächsprotokoll_Beispiel1.json`, "utf8")
          );
        } catch {
          try {
            protocol = JSON.parse(
              await fs.readFile(`${inputDir}/Gesprächsprotokoll.json`, "utf8")
            );
          } catch {
            try {
              protocol = JSON.parse(
                await fs.readFile(`${inputDir}/Unternehmensprofil.json`, "utf8")
              );
            } catch {
              protocol = JSON.parse(
                await fs.readFile(`${inputDir}/Unternehmensprofil2.json`, "utf8")
              );
            }
          }
        }
      }

      logger.info("Protocol loaded (no applicant data)");

      // Build template catalog (with {{variables}})
      const catalog = await buildCatalogTemplate(protocol);

      // Ensure output directory exists
      await fs.mkdir("output", { recursive: true });

      // Write template output
      await fs.writeFile("output/questions_template.json", JSON.stringify(catalog, null, 2), "utf8");

      logger.info("✓ questions_template.json erzeugt: output/questions_template.json");
      console.log("\n✓ questions_template.json erfolgreich erzeugt!");
      console.log(`  Anzahl Fragen: ${catalog.questions.length}`);
      console.log(`  Modus: TEMPLATE (mit {{variables}})`);
      console.log(`  Output: output/questions_template.json`);
      console.log(`\n  ℹ️  Diese Datei enthält {{variable}} Platzhalter.`);
      console.log(`     Nutze Python Variable Injector um Bewerberdaten einzusetzen.`);
      
    } else {
      // ===== NORMAL MODE: With applicant data (backward compatible) =====
      
      // Load input files (try new structure first, then fallback to old)
      let candidate1: any;
      let candidate2: any = null;
      
      try {
        // Try new structure: single Bewerberprofil.json
        candidate1 = JSON.parse(
          await fs.readFile(`${inputDir}/Bewerberprofil.json`, "utf8")
        );
      } catch {
        // Fallback to old structure: Teil1 + Teil2
        candidate1 = JSON.parse(
          await fs.readFile(`${inputDir}/Bewerberprofil_Teil1.json`, "utf8")
        );
        candidate2 = await fs
          .readFile(`${inputDir}/Bewerberprofil_Teil2.json`, "utf8")
          .then(s => JSON.parse(s))
          .catch(() => null);
      }
      
      // Suche nach Gesprächsprotokoll oder Unternehmensprofil
      let protocol: any;
      try {
        protocol = JSON.parse(
          await fs.readFile(`${inputDir}/Gesprächsprotokoll_Beispiel2.json`, "utf8")
        );
      } catch {
        try {
          protocol = JSON.parse(
            await fs.readFile(`${inputDir}/Gesprächsprotokoll_Beispiel1.json`, "utf8")
          );
        } catch {
          try {
            protocol = JSON.parse(
              await fs.readFile(`${inputDir}/Gesprächsprotokoll.json`, "utf8")
            );
          } catch {
            try {
              protocol = JSON.parse(
                await fs.readFile(`${inputDir}/Unternehmensprofil.json`, "utf8")
              );
            } catch {
              protocol = JSON.parse(
                await fs.readFile(`${inputDir}/Unternehmensprofil2.json`, "utf8")
              );
            }
          }
        }
      }

      logger.info("Input files loaded");

      // Build catalog (with actual applicant data)
      const catalog = await buildCatalog(candidate1, candidate2, protocol);

      // Ensure output directory exists
      await fs.mkdir("output", { recursive: true });

      // Write output
      await fs.writeFile("output/questions.json", JSON.stringify(catalog, null, 2), "utf8");

      logger.info("✓ questions.json erzeugt: output/questions.json");
      console.log("\n✓ questions.json erfolgreich erzeugt!");
      console.log(`  Anzahl Fragen: ${catalog.questions.length}`);
      console.log(`  Output: output/questions.json`);
    }
    
  } catch (error: any) {
    logger.error({ error: error.message, stack: error.stack }, "Build failed");
    console.error("\n✗ Fehler beim Erstellen des Fragenkatalogs:");
    console.error(`  ${error.message}`);
    process.exit(1);
  }
}

main();
