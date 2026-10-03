/**
 * Layout choices — the ONLY place the UI names specific signals or commands.
 * Signal labels, groups and descriptions come from the signal store via /fields; this
 * file only decides what goes where on screen (curated Drive tiles, the output
 * catalogue, module list). Edit here, not in components.
 */

export const MODULE_NAME: Record<string, string> = {
  motor: "TD5 (engine)",
  slabs: "SLABS (ABS + air suspension)",
  airbag: "Airbag / SRS",
  ace: "ACE (active cornering)",
  autobox: "Auto gearbox (EAT)",
  bcu: "BCU (body control)",
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
  { id: "airbag", name: "Airbag / SRS", desc: "Read-only by construction. Faults (demo); live read experimental.", tag: "experimental", connectable: true },
  { id: "ace", name: "ACE — Active Cornering", desc: "Fault block isolated, decoding in progress. Demo only on live.", tag: "partial", connectable: true },
  { id: "autobox", name: "Auto gearbox (EAT)", desc: "ReadFaults confirmed, payload undecoded. Demo only on live.", tag: "partial", connectable: true },
  { id: "bcu", name: "BCU — Body Control", desc: "EKA read. No conventional fault memory. Demo only on live.", tag: "partial", connectable: true },
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

/**
 * Body (BCU) vehicle-view zones. `signal` is the snapshot signal name (from the BCU
 * read-inputs). When a signal is absent from the snapshot the zone renders "awaiting
 * mapping" (neutral/dashed) — never a fabricated state. Positions are in the VehicleBase
 * top-down viewBox (0 0 300 460); FRONT is at the top. RHD: driver = right side.
 */
export type LampTone = "accent" | "amber" | "red";
export type BodyLamp = { id: string; signal: string; label: string; x: number; y: number; tone: LampTone };
export const BODY_LAMPS: BodyLamp[] = [
  { id: "ind_fl", signal: "indicator_left", label: "Ind L", x: 56, y: 60, tone: "amber" },
  { id: "side_l", signal: "side_lights", label: "Side", x: 92, y: 50, tone: "accent" },
  { id: "dipped", signal: "dipped", label: "Dipped", x: 150, y: 44, tone: "accent" },
  { id: "main", signal: "main_beam", label: "Main", x: 208, y: 50, tone: "accent" },
  { id: "ind_fr", signal: "indicator_right", label: "Ind R", x: 244, y: 60, tone: "amber" },
  { id: "fog_f", signal: "front_fog", label: "Fog F", x: 150, y: 66, tone: "accent" },
  { id: "brake", signal: "brake_light", label: "Brake", x: 150, y: 414, tone: "red" },
  { id: "reverse", signal: "reverse_light", label: "Rev", x: 108, y: 420, tone: "accent" },
  { id: "fog_r", signal: "rear_fog", label: "Fog R", x: 192, y: 420, tone: "red" },
  { id: "ind_rl", signal: "indicator_left", label: "Ind L", x: 60, y: 420, tone: "amber" },
  { id: "ind_rr", signal: "indicator_right", label: "Ind R", x: 240, y: 420, tone: "amber" },
];
export type BodyDoor = { id: string; signal: string; label: string; place: "frontL" | "frontR" | "front" | "rear" };
export const BODY_DOORS: BodyDoor[] = [
  { id: "driver", signal: "door_driver", label: "Driver", place: "frontR" },
  { id: "passenger", signal: "door_passenger", label: "Passenger", place: "frontL" },
  { id: "bonnet", signal: "bonnet", label: "Bonnet", place: "front" },
  { id: "tailgate", signal: "tailgate", label: "Tailgate", place: "rear" },
];
/** Secondary body states shown as a readout list beside the car. kind: flag | numeric. */
export type BodyReadout = { signal: string; label: string; kind: "flag" | "numeric"; unit?: string; dec?: number };
export const BODY_READOUTS: BodyReadout[] = [
  { signal: "ignition_pos", label: "Ignition pos", kind: "numeric", dec: 0 },
  { signal: "battery", label: "Battery", kind: "numeric", unit: "V", dec: 1 },
  { signal: "heated_screen", label: "Heated screen", kind: "flag" },
  { signal: "wiper_front", label: "Front wiper", kind: "flag" },
  { signal: "wiper_rear", label: "Rear wiper", kind: "flag" },
  { signal: "window_front_left", label: "Window FL", kind: "flag" },
  { signal: "window_front_right", label: "Window FR", kind: "flag" },
];

/** Utilities → raw LID dump: a sensible default request per module. */
export const UTIL_LIDS: Record<string, { example: string; note: string }> = {
  motor: { example: "09 0D 10 1A 1B 1C 40", note: "09 rpm · 1A temps · 1B pedal · 1C boost · 40 injector balance" },
  slabs: { example: "54 43 50 44 56", note: "54 heights · 43 wheel speeds · 50 ABS sensors · 44 supply · 56 door" },
};
