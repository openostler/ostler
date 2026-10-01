import type { ComponentType } from "react";
import { Connect } from "./Connect";
import { Drive } from "./Drive";
import { Faults } from "./Faults";
import { Inputs } from "./Inputs";
import { Outputs } from "./Outputs";
import { Utilities } from "./Utilities";

/** The screen registry: one entry per tab. Add a tab = add one row here.
 * `admin` screens appear only on /admin (password protected by the server). */
export type Screen = { id: string; label: string; component: ComponentType; admin?: boolean };

export const SCREENS: Screen[] = [
  { id: "drive", label: "Drive", component: Drive },
  { id: "connect", label: "Connect", component: Connect },
  { id: "faults", label: "Faults", component: Faults },
  { id: "inputs", label: "Inputs", component: Inputs },
  { id: "outputs", label: "Outputs", component: Outputs },
  { id: "utils", label: "Utilities", component: Utilities },
];

export const screensFor = (admin: boolean): Screen[] => SCREENS.filter((s) => admin || !s.admin);
