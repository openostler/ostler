// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * stylelint with a ratchet (visual design system spec §9, V1d). The rules in
 * stylelint.config.mjs ban raw colours and px font sizes; the stylesheets written before them
 * break them in many places, which V3 migrates page by page. stylelint-baseline.json freezes
 * those: per file, how many times each exact message occurs. A new violation (a message not
 * in the baseline, or more of one) fails; a fixed one asks for the baseline to shrink.
 *
 *   node scripts/lint-css.mjs           check (npm run lint)
 *   node scripts/lint-css.mjs --update  rewrite the baseline after fixing violations
 */
import { readFileSync, writeFileSync } from "node:fs";
import { relative } from "node:path";
import { fileURLToPath } from "node:url";
import stylelint from "stylelint";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const BASELINE = fileURLToPath(new URL("../stylelint-baseline.json", import.meta.url));

const { results } = await stylelint.lint({ files: "src/**/*.css", cwd: ROOT });
/** file → message → count */
const now = {};
for (const r of results) {
  const file = relative(ROOT, r.source).split("\\").join("/");
  for (const w of r.warnings) {
    const counts = (now[file] ??= {});
    counts[w.text] = (counts[w.text] ?? 0) + 1;
  }
  for (const w of r.parseErrors ?? []) console.error(`${file}: ${w.text}`);
}
const sorted = (o) => Object.fromEntries(Object.keys(o).sort().map((k) => [k, typeof o[k] === "object" ? sorted(o[k]) : o[k]]));

if (process.argv.includes("--update")) {
  writeFileSync(BASELINE, `${JSON.stringify(sorted(now), null, 2)}\n`);
  const total = Object.values(now).flatMap(Object.values).reduce((a, b) => a + b, 0);
  console.log(`stylelint baseline: ${total} known violation(s) in ${Object.keys(now).length} file(s)`);
  process.exit(0);
}

let base = {};
try { base = JSON.parse(readFileSync(BASELINE, "utf8")); } catch { /* no baseline: everything is new */ }
const added = [];
const fixed = [];
for (const file of new Set([...Object.keys(now), ...Object.keys(base)])) {
  const a = now[file] ?? {};
  const b = base[file] ?? {};
  for (const msg of new Set([...Object.keys(a), ...Object.keys(b)])) {
    const d = (a[msg] ?? 0) - (b[msg] ?? 0);
    if (d > 0) added.push(`${file}: ${msg}${d > 1 ? ` (${d} new)` : ""}`);
    if (d < 0) fixed.push(`${file}: ${msg}`);
  }
}
if (fixed.length) {
  console.log(`stylelint: ${fixed.length} baselined violation(s) are fixed; run \`node scripts/lint-css.mjs --update\` to shrink the baseline.`);
}
if (added.length) {
  console.error("stylelint: new violations (use a token: var(--…), visual design system spec §9):");
  for (const line of added) console.error(`  ${line}`);
  process.exit(1);
}
console.log("stylelint: no new violations");
