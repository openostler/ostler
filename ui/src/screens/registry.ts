import type { ComponentType } from "react";
import { Capture } from "./Capture";
import { CoverageMap } from "./CoverageMap";
import { Docs } from "./Docs";
import { Drive } from "./Drive";
import { Faults } from "./Faults";
import { Inputs } from "./Inputs";
import { Logs } from "./Logs";
import { ModuleSettings } from "./ModuleSettings";
import { Outputs } from "./Outputs";
import { Utilities } from "./Utilities";

/** The screen registry: one entry per tab. Add a tab = add one row here.
 * `admin` screens appear only on /admin (password protected by the server).
 * `icon` + `short` keep seven tabs on a phone (the short label shows on narrow screens). */
export type Screen = {
  id: string;
  label: string;
  short?: string;
  icon: string;
  component: ComponentType;
  admin?: boolean;
};

export const SCREENS: Screen[] = [
  { id: "drive", label: "Drive", icon: "◔", component: Drive },
  { id: "faults", label: "Faults", icon: "⚠", component: Faults },
  { id: "inputs", label: "Inputs", icon: "↘", component: Inputs },
  { id: "outputs", label: "Outputs", icon: "↗", component: Outputs },
  { id: "settings", label: "Settings", short: "Setup", icon: "≡", component: ModuleSettings },
  { id: "utils", label: "Utilities", short: "Utils", icon: "⚒", component: Utilities },
  { id: "logs", label: "Logs", short: "Logs", icon: "◷", component: Logs },
  // Admin: ids stay "map"/"capture" (App's default admin tab and goTo() links use them).
  { id: "map", label: "Decode", icon: "⇄", component: CoverageMap, admin: true },
  { id: "capture", label: "Label", icon: "✎", component: Capture, admin: true },
  { id: "docs", label: "Docs", icon: "▤", component: Docs, admin: true },
];

export const screensFor = (admin: boolean): Screen[] => SCREENS.filter((s) => admin || !s.admin);
