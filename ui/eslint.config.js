// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";
import tseslint from "typescript-eslint";

// App-model seam 3 (specs/2026-10-06-app-model-design.md §9): one action path. Car actions go
// through `useAction` (api/useAction.ts) and the confirmations in components/confirm.ts; only
// api/client.ts names the action route, and the raw `command()` sender is allowed only in the
// files below, which send server-state commands (port, module, recording, logs, shutdown).
const ACTION_ROUTE = [
  { selector: "Literal[value=/^\\/command\\b/]", message: "Only api/client.ts calls the action route; use useAction()." },
  { selector: "TemplateElement[value.raw=/^\\/command\\b/]", message: "Only api/client.ts calls the action route; use useAction()." },
];
const RAW_COMMAND = {
  patterns: [{
    group: ["**/api/client"], importNames: ["command"],
    message: "Send car actions through useAction() (api/useAction.ts); server-state senders are allowlisted in eslint.config.js.",
  }],
};
const SERVER_STATE_SENDERS = [
  "src/api/useAction.ts",
  "src/state/systems.ts", // select_module
  "src/components/ConnectionSheet.tsx", // port and connection
  "src/components/Preferences.tsx", // shutdown
  "src/components/RecordingCard.tsx", // split_session
  "src/components/replay/Replay.tsx", // delete_session
  "src/lib/recordingOptions.ts", // recording_options
  "src/screens/Capture.tsx", // read_block (Tier 0)
  "src/screens/Faults.tsx", // read_all_faults, set_fault_watch
  "src/screens/Inputs.tsx", // start_csv, stop_csv
];

// Visual design system spec §9 (V1d): colours and type come from the design tokens, never a
// raw hex/rgb() value or an inline fontSize in TS/TSX (Canvas and MapLibre read tokens through
// lib/token.ts). Existing uses are frozen in eslint-suppressions.json until V3 migrates them; a
// new one fails `npm run lint`. Token files and tests are exempt.
const RAW_COLOUR = /(^|[\s,(:])#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b|\b(?:rgba?|hsla?)\(/;
const ostler = {
  rules: {
    "no-raw-style": {
      meta: {
        type: "problem",
        docs: { description: "Colours and font sizes come from the design tokens" },
        messages: {
          colour: "Raw colour: use a token (var(--…) in CSS, token() for Canvas/MapLibre). Visual spec §9.",
          fontSize: "Inline fontSize: use a type token in CSS (var(--type-…)). Visual spec §9.",
        },
        schema: [],
      },
      create(context) {
        const check = (node, text) => { if (typeof text === "string" && RAW_COLOUR.test(text)) context.report({ node, messageId: "colour" }); };
        return {
          Literal: (node) => check(node, node.value),
          TemplateElement: (node) => check(node, node.value.raw),
          "JSXAttribute[name.name='style'] Property[key.name='fontSize']": (node) => context.report({ node, messageId: "fontSize" }),
        };
      },
    },
  },
};

export default tseslint.config(
  { ignores: ["node_modules", "test-results", "playwright-report"] },
  {
    files: ["**/*.{ts,tsx}"],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: { ecmaVersion: 2022, globals: { ...globals.browser, ...globals.node } },
    plugins: { "react-hooks": reactHooks, "react-refresh": reactRefresh },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    },
  },
  {
    files: ["src/**/*.{ts,tsx}"],
    ignores: ["src/**/*.test.{ts,tsx}", "src/test/**"],
    rules: {
      "no-restricted-syntax": ["error", ...ACTION_ROUTE],
      "no-restricted-imports": ["error", RAW_COMMAND],
    },
  },
  {
    files: ["src/**/*.{ts,tsx}"],
    ignores: ["src/**/*.test.{ts,tsx}", "src/test/**"],
    plugins: { ostler },
    rules: { "ostler/no-raw-style": "error" },
  },
  { files: ["src/api/client.ts"], rules: { "no-restricted-syntax": "off" } },
  { files: SERVER_STATE_SENDERS, rules: { "no-restricted-imports": "off" } },
);
