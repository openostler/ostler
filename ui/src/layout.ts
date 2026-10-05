/**
 * Layout choices — the ONLY place the UI names specific signals or commands.
 * Signal labels, groups and descriptions come from the signal store via /fields; this
 * file only decides what goes where on screen (curated Drive tiles, the body view, the
 * raw-LID presets). Outputs, Settings and Utilities come from /catalog. Edit here, not in
 * components.
 */

export const MODULE_NAME: Record<string, string> = {
  motor: "TD5 (engine)",
  slabs: "SLABS (ABS + air suspension)",
  airbag: "SRS (airbag)",
  ace: "ACE (active cornering)",
  autobox: "EAT (auto gearbox)",
  bcu: "BCU (body control)",
};
export const moduleName = (m: string): string => MODULE_NAME[m] ?? m;

/** Display order of signal groups (a group not listed here sorts after these). */
export const GROUP_ORDER = [
  "Engine", "Temperatures", "Fuelling", "Pressures", "Accelerator",
  "Ride height", "Wheels", "Electrical", "Inputs", "Other",
];

/**
 * Driver's dashboard (TD5): two hero gauges for what moves while driving, then stat
 * tiles with a range bar and the last minute. Speed and rpm are already on the cluster,
 * so they are left out. Fuel is shown in L/mil (Swedish litres per 10 km): the server's
 * L/100km ÷ 10. SLABS uses the car diagram instead (SlabsCar).
 */
export type DriveTile = {
  label: string;
  signal: string;
  gauge?: boolean;
  dec?: number;
  unit?: string;
  conv?: (v: number) => number;
};
const per10km = (v: number) => v / 10;
export const DRIVE_TILES: DriveTile[] = [
  { signal: "manifold_press", label: "Boost", gauge: true, dec: 2 },
  { signal: "coolant_temp", label: "Coolant", gauge: true, dec: 0 },
  { signal: "battery", label: "Battery", dec: 1 },
  { signal: "air_temp", label: "Intake air", dec: 0 },
  { signal: "economy", label: "Fuel now", conv: per10km, unit: "L/mil", dec: 2 },
  { signal: "trip_economy", label: "Trip", conv: per10km, unit: "L/mil", dec: 2 },
];

/**
 * Body (BCU) vehicle view. `BODY_SIGNALS` is the only place the UI names the BCU read-input
 * signals; the SVG overlay (BodyCar) reads them to light the car's own lamp clusters, and
 * `BODY_GROUPS` drives the category-grouped readout list below. A signal absent from the
 * snapshot renders "awaiting mapping" — never a fabricated state. RHD: driver = right side.
 */
export const BODY_SIGNALS = {
  side: "side_lights", dipped: "dipped", main: "main_beam", frontFog: "front_fog", rearFog: "rear_fog",
  indL: "indicator_left", indR: "indicator_right", hazard: "hazard", brake: "brake_light", reverse: "reverse_light",
  doorDriver: "door_driver", doorPassenger: "door_passenger", bonnet: "bonnet", tailgate: "tailgate",
  winFL: "window_front_left", winFR: "window_front_right",
  wiperF: "wiper_front", wiperR: "wiper_rear", heated: "heated_screen",
  ignition: "ignition_pos", battery: "battery",
} as const;

export type BodyRow = { signal: string; label: string; kind: "flag" | "num"; unit?: string; dec?: number };
export type BodyGroup = { title: string; items: BodyRow[] };
export const BODY_GROUPS: BodyGroup[] = [
  {
    title: "Lighting", items: [
      { signal: "side_lights", label: "Side lights", kind: "flag" },
      { signal: "dipped", label: "Dipped beam", kind: "flag" },
      { signal: "main_beam", label: "Main beam", kind: "flag" },
      { signal: "front_fog", label: "Front fog", kind: "flag" },
      { signal: "rear_fog", label: "Rear fog", kind: "flag" },
      { signal: "indicator_left", label: "Left indicator", kind: "flag" },
      { signal: "indicator_right", label: "Right indicator", kind: "flag" },
      { signal: "hazard", label: "Hazard", kind: "flag" },
      { signal: "brake_light", label: "Brake lights", kind: "flag" },
      { signal: "reverse_light", label: "Reverse light", kind: "flag" },
    ],
  },
  {
    title: "Doors & openings", items: [
      { signal: "door_driver", label: "Driver door", kind: "flag" },
      { signal: "door_passenger", label: "Passenger door", kind: "flag" },
      { signal: "bonnet", label: "Bonnet", kind: "flag" },
      { signal: "tailgate", label: "Tailgate", kind: "flag" },
    ],
  },
  {
    title: "Windows", items: [
      { signal: "window_front_left", label: "Front left", kind: "flag" },
      { signal: "window_front_right", label: "Front right", kind: "flag" },
    ],
  },
  {
    title: "Wash / wipe", items: [
      { signal: "wiper_front", label: "Front wiper", kind: "flag" },
      { signal: "wiper_rear", label: "Rear wiper", kind: "flag" },
    ],
  },
  { title: "Climate", items: [{ signal: "heated_screen", label: "Heated screen", kind: "flag" }] },
  {
    title: "Power", items: [
      { signal: "ignition_pos", label: "Ignition position", kind: "num", dec: 0 },
      { signal: "battery", label: "Battery", kind: "num", unit: "V", dec: 1 },
    ],
  },
];

/** Utilities → raw LID dump: a sensible default request per module. */
export const UTIL_LIDS: Record<string, { example: string; note: string }> = {
  motor: { example: "09 0D 10 1A 1B 1C 40", note: "09 rpm · 1A temps · 1B pedal · 1C boost · 40 injector balance" },
  slabs: { example: "54 43 50 44 56", note: "54 heights · 43 wheel speeds · 50 ABS sensors · 44 supply · 56 door" },
};
