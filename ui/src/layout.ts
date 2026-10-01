/**
 * Layout choices — the ONLY place the UI names specific signals or commands.
 * Signal labels, groups and descriptions come from the signal store via /fields; this
 * file only decides what goes where on screen (curated Drive tiles, the output
 * catalogue, module list). Edit here, not in components.
 */

export const MODULE_NAME: Record<string, string> = {
  motor: "TD5 (engine)",
  slabs: "SLABS (ABS + air suspension)",
};
export const moduleName = (m: string): string => MODULE_NAME[m] ?? m;

/** Display order of signal groups (a group not listed here sorts after these). */
export const GROUP_ORDER = [
  "Engine", "Temperatures", "Fuelling", "Pressures", "Accelerator",
  "Ride height", "Wheels", "Electrical", "Inputs", "Other",
];

export type ModuleTag = "verified" | "experimental" | "partial";
export const MODULES: { id: string; name: string; desc: string; tag: ModuleTag; connectable: boolean }[] = [
  { id: "motor", name: "TD5 — Engine ECU", desc: "Faults, inputs, outputs. Validated on the car.", tag: "verified", connectable: true },
  { id: "slabs", name: "SLABS — ABS + Air Suspension", desc: "Faults, heights, actuator tests, ABS bleed.", tag: "verified", connectable: true },
  { id: "airbag", name: "Airbag / SRS", desc: "Read-only by construction. Faults only.", tag: "experimental", connectable: false },
  { id: "ace", name: "ACE — Active Cornering", desc: "Fault block isolated, decoding in progress.", tag: "partial", connectable: false },
  { id: "autobox", name: "Auto gearbox (EAT)", desc: "ReadFaults confirmed, payload undecoded.", tag: "partial", connectable: false },
  { id: "bcu", name: "BCU — Body Control", desc: "EKA read. No conventional fault memory.", tag: "partial", connectable: false },
];

/**
 * Driver's dashboard: what matters on the move and is NOT already on the cluster (so no
 * speed/rpm). Grid flow on 4 columns, cards span 2; keep gauges paired so rows stay clean.
 * Fuel in L/mil (Swedish litres per 10 km) from the server's L/100km, so ÷10.
 */
export type DriveTile = {
  label: string;
  clock?: boolean;
  signal?: string;
  gauge?: { min: number; max: number };
  dec?: number;
  unit?: string;
  conv?: (v: number) => number;
};
const per10km = (v: number) => v / 10;
export const DRIVE_TILES: DriveTile[] = [
  { clock: true, label: "Time" },
  { signal: "battery", label: "Battery" },
  { signal: "manifold_press", label: "Boost", gauge: { min: 1.0, max: 2.5 }, dec: 1 },
  { signal: "coolant_temp", label: "Coolant", gauge: { min: 40, max: 120 }, dec: 0 },
  { signal: "economy", label: "Fuel", conv: per10km, unit: "L/mil", dec: 1 },
  { signal: "trip_economy", label: "Trip", conv: per10km, unit: "L/mil", dec: 1 },
  { signal: "air_temp", label: "Intake" },
  { signal: "lifetime_economy", label: "Lifetime", conv: per10km, unit: "L/mil", dec: 1 },
];

/** Actuator tests per module — real /command actions (see web/sources.py). */
export type OutputButton = { action: string; label: string; warn?: boolean };
export type OutputDef = {
  group: string;
  name: string;
  cmd: string; // the K-line request, shown for reference
  tag: "verified" | "experimental";
  buttons: OutputButton[];
};
const run = (action: string, warn = true): OutputButton[] => [{ action, label: "Run", warn }];
export const OUTPUTS: Record<string, OutputDef[]> = {
  slabs: [
    { group: "ABS", name: "ABS pump", cmd: "31 25 08/02 fa", tag: "verified",
      buttons: [{ action: "pump_on", label: "On", warn: true }, { action: "pump_off", label: "Off" }] },
    { group: "ABS", name: "Valve test FL", cmd: "31 22 11 0c", tag: "verified", buttons: run("wheel_fl") },
    { group: "ABS", name: "Valve test FR", cmd: "31 22 10 03", tag: "verified", buttons: run("wheel_fr") },
    { group: "ABS", name: "Valve test RL", cmd: "31 22 13 c0", tag: "verified", buttons: run("wheel_rl") },
    { group: "ABS", name: "Valve test RR", cmd: "31 22 12 30", tag: "verified", buttons: run("wheel_rr") },
    { group: "ABS bleed ⚠ brakes", name: "Power bleed", cmd: "31 22 04 00 49c4/40 00", tag: "verified",
      buttons: [{ action: "bleed_power_on", label: "Start", warn: true }, { action: "bleed_power_off", label: "Stop" }] },
    { group: "ABS bleed ⚠ brakes", name: "Module bleed (4 steps)", cmd: "31 22 11..14", tag: "verified",
      buttons: run("bleed_module") },
    { group: "Air suspension", name: "Left corner", cmd: "31 33/35 28", tag: "verified",
      buttons: [{ action: "raise_left", label: "Raise", warn: true }, { action: "lower_left", label: "Lower", warn: true }] },
    { group: "Air suspension", name: "Right corner", cmd: "31 34/36 28", tag: "verified",
      buttons: [{ action: "raise_right", label: "Raise", warn: true }, { action: "lower_right", label: "Lower", warn: true }] },
    { group: "Air suspension", name: "Compressor test", cmd: "31 30 28", tag: "verified", buttons: run("compressor") },
    { group: "Air suspension", name: "Exhaust valve test", cmd: "31 2f 28", tag: "verified", buttons: run("exhaust") },
    { group: "Air suspension", name: "Buzzer test", cmd: "31 31 0a", tag: "verified", buttons: run("buzzer", false) },
  ],
  motor: [
    { group: "Lamps & relays", name: "Fuel pump", cmd: "30 A1 FF", tag: "experimental", buttons: run("output_fuel_pump") },
    { group: "Lamps & relays", name: "MIL lamp", cmd: "30 A2 FF", tag: "experimental", buttons: run("output_mil_lamp", false) },
    { group: "Lamps & relays", name: "A/C clutch", cmd: "30 A3 FF", tag: "experimental", buttons: run("output_ac_clutch") },
    { group: "Lamps & relays", name: "A/C fan", cmd: "30 A4 FF", tag: "experimental", buttons: run("output_ac_fan") },
    { group: "Lamps & relays", name: "Glow plugs", cmd: "30 B3 FF", tag: "experimental", buttons: run("output_glow_plugs") },
    { group: "Lamps & relays", name: "Rev counter", cmd: "30 B7 FF", tag: "experimental", buttons: run("output_rev_counter", false) },
    { group: "Lamps & relays", name: "Temp gauge", cmd: "30 BA FF", tag: "experimental", buttons: run("output_temp_gauge", false) },
    { group: "Boost & EGR", name: "Wastegate", cmd: "30 BE …PWM", tag: "experimental", buttons: run("output_wastegate") },
    { group: "Boost & EGR", name: "EGR throttle", cmd: "30 BD …PWM", tag: "experimental", buttons: run("output_egr_throttle") },
    ...[1, 2, 3, 4, 5].map((n): OutputDef => ({
      group: "Injectors", name: `Injector ${n} click`, cmd: `31 C2 0${n}`, tag: "experimental",
      buttons: run(`injector_${n}`),
    })),
  ],
};

/** Utilities → raw LID dump: a sensible default request per module. */
export const UTIL_LIDS: Record<string, { example: string; note: string }> = {
  motor: { example: "09 0D 10 1A 1B 1C 40", note: "09 rpm · 1A temps · 1B pedal · 1C boost · 40 injector balance" },
  slabs: { example: "54 43 50 44 56", note: "54 heights · 43 wheel speeds · 50 ABS sensors · 44 supply · 56 door" },
};
