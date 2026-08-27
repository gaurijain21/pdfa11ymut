import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "outputs";
const raw = JSON.parse(await fs.readFile(`${outputDir}/pdfa11ymut_detection_analysis_data.json`, "utf8"));

const workbook = Workbook.create();

function addSheet(name, rows) {
  const sheet = workbook.worksheets.add(name);
  if (!rows.length) return sheet;
  const headers = Object.keys(rows[0]);
  const data = [headers, ...rows.map((row) => headers.map((h) => row[h]))];
  const range = sheet.getRangeByIndexes(0, 0, data.length, headers.length);
  range.values = data;
  sheet.getRangeByIndexes(0, 0, 1, headers.length).format = {
    fill: "#1F4E79",
    font: { bold: true, color: "#FFFFFF" },
  };
  range.format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
  range.format.wrapText = true;
  sheet.freezePanes.freezeRows(1);
  for (let i = 0; i < headers.length; i += 1) {
    sheet.getRangeByIndexes(0, i, data.length, 1).format.columnWidth = Math.min(
      Math.max(headers[i].length + 4, 14),
      ["short_mutation_description", "expected_accessibility_effect", "interpretation_note", "veraPDF_failed_rule"].includes(headers[i]) ? 44 : 24,
    );
  }
  sheet.getRangeByIndexes(1, 0, Math.max(data.length - 1, 1), headers.length).format.rowHeight = 48;
  return sheet;
}

const summaryRows = [
  { metric: "Generated and independently verified mutants", value: 23, note: "Denominator for detection rates." },
  { metric: "Non-generated/N/A cases", value: 2, note: "G05_M03 and G05_M05 preserved as N/A." },
  { metric: "PAC detection rate", value: "4/23 = 17.4%", note: "Detected only generated M03 mutants." },
  { metric: "Acrobat detection rate", value: "5/23 = 21.7%", note: "Detected M03 mutants plus G02_M04." },
  { metric: "veraPDF detection rate", value: "5/23 = 21.7%", note: "Detected M03 mutants plus G02_M04." },
  { metric: "Only validator disagreement case", value: "G02_M04", note: "PAC missed; Acrobat and veraPDF detected list-structure failures." },
  { metric: "Interpretation boundary", value: "Mutation detection, not full accuracy", note: "Missed means no relevant automated failure despite independent mutation verification." },
];

const summarySheet = addSheet("Summary", summaryRows);
summarySheet.getRange("A:A").format.columnWidth = 30;
summarySheet.getRange("B:B").format.columnWidth = 20;
summarySheet.getRange("C:C").format.columnWidth = 62;
summarySheet.getRange("A2:C8").format.rowHeight = 86;
summarySheet.getRange("A1:C8").format.verticalAlignment = "center";
addSheet("Detection Matrix", raw.matrix);
addSheet("Overall Rates", raw.overall);
addSheet("Per Operator Rates", raw.per_operator);
addSheet("Agreement", raw.pairwise_agreement);
addSheet("Patterns", raw.patterns);

const rqRows = [
  { id: "RQ1", text: "To what extent do automated PDF accessibility validators detect independently verified structure-only accessibility mutations in otherwise validator-clean PDF/UA-oriented documents?" },
  { id: "RQ2", text: "Are detection outcomes concentrated in particular mutation operators, such as heading-hierarchy violations, rather than distributed evenly across reading-order, omission, list/table association, and MCID-order defects?" },
  { id: "RQ3", text: "How much do commonly used validators agree or disagree on the same controlled PDF accessibility mutants, and which mutation cases explain disagreement?" },
  { id: "RQ4", text: "What does mutation-based evaluation reveal about the boundary between machine-checkable conformance failures and verified accessibility-relevant defects that survive automated checking?" },
];
addSheet("Research Questions", rqRows);

const notesRows = [
  { topic: "Golden baseline", finding: "All five goldens passed veraPDF PDF/UA-1. Prior recorded PAC and Acrobat runs also reported clean automated baselines." },
  { topic: "Independent verification", finding: "Generated mutants are treated as verified defects because mutation_verification.csv records generation_success, parseability, unchanged page counts, mutation_verified, no unexpected structural changes, and no visual difference." },
  { topic: "PAC", finding: "PAC detected four M03 mutants and missed the remaining generated verified mutants, including G02_M04." },
  { topic: "Acrobat", finding: "Acrobat detected the same four M03 mutants plus G02_M04; goldens had 0 automated failures, with two normal manual-check items." },
  { topic: "veraPDF", finding: "veraPDF detected the same four M03 mutants plus G02_M04 under PDF/UA-1 profile with 106 rules." },
  { topic: "Caution", finding: "Do not phrase the detection rates as general checker accuracy. They are mutation-detection rates on this specific controlled benchmark and validator configuration." },
];
addSheet("Discussion Notes", notesRows);

const preview = await workbook.render({
  sheetName: "Summary",
  autoCrop: "all",
  scale: 1,
  format: "png",
});
await fs.writeFile(`${outputDir}/pdfa11ymut_detection_workbook_preview.png`, new Uint8Array(await preview.arrayBuffer()));

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(`${outputDir}/pdfa11ymut_detection_analysis.xlsx`);

const check = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 3000,
  tableMaxRows: 4,
  tableMaxCols: 5,
});
console.log(check.ndjson);
