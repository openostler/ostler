// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Visual design system spec §9 (V1d): colours and font sizes come from the design tokens
 * (ui/tokens/*.tokens.json → var(--…)), never raw values in a stylesheet. The token files are
 * JSON, so the only CSS here is ours. Existing violations are frozen in stylelint-baseline.json
 * (scripts/lint-css.mjs) until V3 migrates the pages; a new one fails `npm run lint`.
 */
export default {
  plugins: ["stylelint-declaration-strict-value"],
  rules: {
    "color-no-hex": true,
    "color-named": "never",
    "function-disallowed-list": ["rgb", "rgba", "hsl", "hsla", "hwb", "lab", "lch", "oklab", "oklch"],
    "declaration-property-unit-disallowed-list": { "font-size": ["px"], font: ["px"] },
    "scale-unlimited/declaration-strict-value": [
      ["/color$/", "fill", "stroke", "font-size"],
      {
        ignoreValues: ["transparent", "currentColor", "currentcolor", "inherit", "initial", "unset", "none", "/^-?[\\d.]+(em|rem|%)$/"],
        disableFix: true,
      },
    ],
  },
};
