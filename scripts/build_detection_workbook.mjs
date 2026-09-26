// The historical workbook builder embedded old summary values. The active
// workbook must be generated from analysis/generated/*.csv after evidence is
// available. This guard makes accidental reuse fail loudly instead of writing
// stale numbers.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const summary = path.join(root, "analysis", "generated", "metrics_summary.json");
if (!fs.existsSync(summary)) {
  console.error("No active analysis summary exists. Run python scripts/rebuild_analysis.py first.");
  process.exit(1);
}
const data = JSON.parse(fs.readFileSync(summary, "utf8"));
console.log(JSON.stringify({ status: data.status, source: "analysis/generated/metrics_summary.json", note: "Workbook export intentionally deferred until canonical evidence is available." }, null, 2));
