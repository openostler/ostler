/**
 * The HTTP contract with the Python server (src/openostler/web/server.py), as Zod schemas.
 *
 * Every response is validated at runtime, so a server change surfaces as a clear error
 * instead of `undefined` deep in a component. tests/test_ui_contract.py keeps the
 * fixtures in ./fixtures in sync with the real server; schemas.test.ts parses them here.
 * Change a schema → regenerate fixtures (UPDATE_UI_FIXTURES=1 pytest tests/test_ui_contract.py).
 */
import { z } from "zod";

/** Confidence of a mapping: verified against the car, or derived/unverified (ADR-0006). */
export const Confidence = z.string(); // "proven" | "candidate"; open so a new level doesn't crash the UI
export type Confidence = z.infer<typeof Confidence>;

/** One live value in a snapshot: v value, u unit, s range status, c confidence. */
export const SignalValue = z.object({
  v: z.number().nullable(),
  u: z.string().default(""),
  s: z.string().nullable().optional(), // "ok" | "low" | "high" | "suspect" | null
  c: Confidence.optional(),
});
export type SignalValue = z.infer<typeof SignalValue>;

export const Logging = z.object({
  recording: z.boolean(),
  file: z.string().optional(),
  rows: z.number().optional(),
});

export const PortInfo = z.object({
  spec: z.string(),
  resolved: z.string().nullable(),
  candidates: z.array(z.string()).default([]),
});
export type PortInfo = z.infer<typeof PortInfo>;

export const ActiveTest = z.object({
  action: z.string(),
  label: z.string(),
  since: z.number(),
  stop: z.string(),
});
export type ActiveTest = z.infer<typeof ActiveTest>;

/** Latest GPS fix (null when there is no GPS source). ADR-0009. */
export const GpsFix = z.object({
  fix: z.boolean(),
  lat: z.number().nullable(),
  lon: z.number().nullable(),
  speed_kmh: z.number().nullable(),
  heading: z.number().nullable(),
  sats: z.number().nullable(),
  hdop: z.number().nullable(),
  src: z.string(), // "usb" | "mock" | "replay"
  age_s: z.number().nullable(),
});
export type GpsFix = z.infer<typeof GpsFix>;

/** The session being recorded right now (null when idle). */
export const Recording = z.object({
  session: z.string(),
  since: z.number(),
  rows: z.number(),
  /** "recording" while connected; "paused" while the car is disconnected (no rows written). */
  state: z.string().optional(), // absent = "recording" (older servers)
});
export type Recording = z.infer<typeof Recording>;

/** The snapshot pushed over /events every poll (and returned by /snapshot). */
export const Snapshot = z.object({
  status: z.string(), // "connected" | "connecting" | "error" | "no-cable"
  source: z.string().optional(),
  module: z.string().optional(), // canonical module id (a /pack module id)
  mode: z.string().nullable().optional(), // "mock" | "live"
  modes: z.array(z.string()).optional(),
  signals: z.record(z.string(), SignalValue).default({}),
  faults: z.array(z.string()).default([]),
  logging: Logging.optional(),
  public: z.boolean().optional(),
  fault_watch: z.boolean().optional(),
  allow_shutdown: z.boolean().optional(),
  error: z.string().optional(),
  stale: z.boolean().optional(),
  connect_phase: z.string().nullable().optional(),
  /** Connection state (ADR-0008 spec): disconnected|connecting|connected|lost|reconnecting|error. */
  conn: z.string().optional(),
  /** Server epoch seconds of this snapshot. */
  ts: z.number().optional(),
  /** Car battery in volts, or null when unknown. */
  battery_v: z.number().nullable().optional(),
  port: PortInfo.optional(),
  /** A latched test that is still on (ActiveTestBanner), else null. */
  active_test: ActiveTest.nullable().optional(),
  gps: GpsFix.nullable().optional(),
  recording: Recording.nullable().optional(),
  recording_sources: z.lazy(() => RecordingSources).nullable().optional(),
});
export type Snapshot = z.infer<typeof Snapshot>;

/** Expected fields per module, with presentation metadata from the signal store. */
export const Field = z.object({
  name: z.string(),
  unit: z.string(),
  c: Confidence,
  limits: z.tuple([z.number(), z.number()]).nullable(),
  label: z.string(),
  group: z.string(),
  description: z.string(),
  derived: z.boolean(),
  /** What a bar or gauge draws, low → high (null: no bar). */
  span: z.tuple([z.number(), z.number()]).nullable(),
  /** The healthy band shaded on it (null: no band). Status still comes from `limits`. */
  normal: z.tuple([z.number(), z.number()]).nullable(),
});
export type Field = z.infer<typeof Field>;
export const FieldsResponse = z.object({ module: z.string(), fields: z.array(Field) });

/** One fault code's meaning (the `dtc` store) — served by /faults. Open fields default
 * to "" because the store omits empty ones. */
export const FaultMeaning = z.object({
  key: z.string(),
  name: z.string(),
  description: z.string().default(""),
  cause: z.string().default(""),
  severity: z.string().default(""),
  system: z.string().default(""),
  pcode: z.string().default(""),
  source: z.string().default(""),
});
export type FaultMeaning = z.infer<typeof FaultMeaning>;
export const FaultsResponse = z.object({ module: z.string(), faults: z.array(FaultMeaning) });

export const MapItem = z.object({
  name: z.string(),
  status: z.string(), // "ok" | "maybe" | "todo"
  ref: z.string().optional(),
  lid: z.string().optional(),
  sig: z.string().optional(),
});
export type MapItem = z.infer<typeof MapItem>;
export const MapCategory = z.object({ cat: z.string(), items: z.array(MapItem) });
export type MapCategory = z.infer<typeof MapCategory>;
export const Coverage = z.object({ ok: z.number(), maybe: z.number(), total: z.number() });
export const MapResponse = z.object({
  module: z.string(),
  map: z.array(MapCategory),
  modules: z.array(z.string()),
  coverage: z.record(z.string(), Coverage),
});
export type MapResponse = z.infer<typeof MapResponse>;

export const SniffDecode = z.object({
  name: z.string(),
  value: z.union([z.number(), z.string()]).nullable(),
  unit: z.string().optional(),
  offset: z.number().optional(),
  kind: z.string().optional(),
});
export const SniffLid = z.object({
  lid: z.string(),
  raw: z.string(),
  count: z.number(),
  decode: z.array(SniffDecode).default([]),
});
export type SniffLid = z.infer<typeof SniffLid>;
export const SniffResponse = z.object({
  module: z.string().nullable(),
  modules: z.array(z.string()),
  lids: z.array(SniffLid),
  status: z.string().optional(), // "starting" | "live" | "empty" | "error"; absent = no sniffer
  error: z.string().nullable().optional(),
  source: z.string().optional(),
  frames: z.number().optional(),
  lines: z.number().optional(),
  age: z.number().nullable().optional(),
});
export type SniffResponse = z.infer<typeof SniffResponse>;

export const DocsResponse = z.object({
  docs: z.array(z.object({ id: z.string(), title: z.string(), group: z.string() })),
});
export type DocEntry = z.infer<typeof DocsResponse>["docs"][number];

export const Community = z.object({
  consent: z.boolean().nullable(),
  endpoint: z.string().nullable(),
  vehicle: z.record(z.string(), z.unknown()).nullable().optional(),
  install: z.string().optional(),
  registered: z.boolean().optional(),
  pending: z.number().optional(),
});
export type Community = z.infer<typeof Community>;

export const FaultScanEntry = z.object({
  module: z.string(),
  status: z.string(), // "ok" | "faults" | "error" | "unimplemented"
  faults: z.array(z.string()).default([]),
  error: z.string().optional(),
  note: z.string().optional(),
});
export type FaultScanEntry = z.infer<typeof FaultScanEntry>;

/** Every /command reply: {ok, message|error} plus action-specific extras. */
export const CommandReply = z.looseObject({
  ok: z.boolean(),
  message: z.string().optional(),
  error: z.string().optional(),
  file: z.string().optional(),
  path: z.string().optional(),
  rows: z.number().optional(),
  fault_watch: z.boolean().optional(),
  mode: z.string().nullable().optional(),
  module: z.string().optional(),
  raws: z.record(z.string(), z.string()).optional(),
  report: z.array(FaultScanEntry).optional(),
  shutting_down: z.boolean().optional(),
});
export type CommandReply = z.infer<typeof CommandReply>;

export const AutomapReply = z.looseObject({
  ok: z.boolean(),
  error: z.string().optional(),
  mode: z.string().optional(), // "numeric" | "state"
  lid: z.string().optional(),
  offset: z.number().optional(),
  kind: z.string().optional(),
  scale: z.number().optional(),
  bias: z.number().optional(),
  r2: z.number().optional(),
  clean: z.boolean().optional(),
  how: z.string().optional(),
  signal: z.string().optional(),
  bit: z.number().nullable().optional(),
  rule: z.string().optional(),
  mapping: z.record(z.string(), z.number()).optional(),
  diff: z
    .array(z.object({ lid: z.string(), byte: z.number(), values: z.array(z.number()) }))
    .optional(),
});
export type AutomapReply = z.infer<typeof AutomapReply>;

export const OkReply = z.looseObject({
  ok: z.boolean(),
  error: z.string().optional(),
  stored: z.boolean().optional(),
  module: z.string().optional(),
  name: z.string().optional(),
  consent: z.boolean().optional(),
  queued: z.boolean().optional(),
});
export type OkReply = z.infer<typeof OkReply>;

/* ---- /catalog (ADR-0008, specs/2026-10-05-ui-overhaul-design.md) ---- */

/** Item status: verified | candidate | sniff | untranscribed (open: a new level must not crash). */
export const ItemStatus = z.string();
/** Safety class: read | actuator | service | gated. */
export const Safety = z.string();

export const CatalogCoverage = z.object({
  verified: z.number(),
  candidate: z.number(),
  sniff: z.number(),
  untranscribed: z.number(),
  total: z.number(),
});
export type CatalogCoverage = z.infer<typeof CatalogCoverage>;

/** One runnable (or planned/gated) action from the command registry (src/openostler/commands.py). */
export const CatalogAction = z.object({
  action: z.string(),
  label: z.string(),
  status: z.string(), // "verified" | "experimental" | "planned"
  safety: Safety,
  confirm: z.string(), // "none" | "preconditions" | "typed"
  preconditions: z.array(z.string()).default([]),
  stop: z.string().optional(),
  ref: z.string().default(""),
});
export type CatalogAction = z.infer<typeof CatalogAction>;

export const CatalogItem = z.object({
  id: z.string(),
  name: z.string(),
  status: ItemStatus,
  safety: Safety,
  sig: z.string().nullable().optional(),
  lid: z.string().nullable().optional(),
  ref: z.string().default(""),
  note: z.string().default(""),
  placeholder: z.boolean().default(false),
  pages: z.number().nullable().optional(),
  actions: z.array(CatalogAction).default([]),
});
export type CatalogItem = z.infer<typeof CatalogItem>;

export const CatalogGroup = z.object({
  id: z.string(),
  title: z.string(),
  parent: z.string().nullable().optional(),
  nanocom: z.string().nullable().optional(),
  items: z.array(CatalogItem),
});
export type CatalogGroup = z.infer<typeof CatalogGroup>;

export const CatalogPage = z.object({
  id: z.string(), // "faults" | "inputs" | "outputs" | "settings" | "utilities"
  title: z.string(),
  coverage: CatalogCoverage,
  groups: z.array(CatalogGroup),
});
export type CatalogPage = z.infer<typeof CatalogPage>;

export const Catalog = z.object({
  module: z.string(),
  store_module: z.string(),
  coverage: CatalogCoverage,
  pages: z.array(CatalogPage),
});
export type Catalog = z.infer<typeof Catalog>;

export const CatalogModule = z.object({
  module: z.string(),
  store_module: z.string(),
  name: z.string(),
  coverage: CatalogCoverage,
});
export type CatalogModule = z.infer<typeof CatalogModule>;
export const CatalogModules = z.object({ modules: z.array(CatalogModule) });

/* ---- /sessions (ADR-0009, specs/2026-10-05-session-logbook-design.md) ---- */

export const SessionChannel = z.object({
  name: z.string(),
  units: z.string().default(""),
  group: z.string().default(""),
  c: z.string().nullable().optional(), // store confidence; null for GPS/accel
  limits: z.tuple([z.number(), z.number()]).nullable().optional(),
});
export type SessionChannel = z.infer<typeof SessionChannel>;
const LonLat = z.tuple([z.number(), z.number()]);

export const Place = z.object({
  label: z.string(),
  source: z.string(), // "geonames" | "osm"
  label_offline: z.string().nullable().optional(),
});
export type Place = z.infer<typeof Place>;

export const SessionMeta = z.object({
  id: z.string(),
  name: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  place: Place.nullable().optional(),
  place_start: Place.nullable().optional(),
  place_end: Place.nullable().optional(),
  note_count: z.number().optional(),
  start_utc: z.string(),
  end_utc: z.string().nullable(),
  duration_s: z.number(),
  rows: z.number(),
  parts: z.array(z.string()).default([]),
  modules: z.array(z.string()).default([]),
  channels: z.array(SessionChannel).default([]),
  has_gps: z.boolean(),
  distance_km: z.number(),
  max_speed_kmh: z.number().nullable(),
  bbox: z.tuple([z.number(), z.number(), z.number(), z.number()]).nullable(),
  start_pos: LonLat.nullable(),
  end_pos: LonLat.nullable(),
  synthetic: z.boolean(),
  recording: z.boolean(),
  source: z.string(), // "mock" | "live" | "demo"
  audio: z.array(z.lazy(() => AudioTrack)).default([]),
  accel_cal: z.lazy(() => AccelCal).nullable().optional(),
});
export type SessionMeta = z.infer<typeof SessionMeta>;
export const SessionList = z.object({ sessions: z.array(SessionMeta), next: z.string().nullable().optional() });
export const SessionHistogram = z.object({
  group: z.string(), // "month" | "day"
  buckets: z.array(z.object({ key: z.string(), count: z.number(), km: z.number() })),
});
export type SessionHistogram = z.infer<typeof SessionHistogram>;
export const SessionMetaReply = z.looseObject({ ok: z.boolean(), error: z.string().optional(), meta: SessionMeta.optional() });

/** Columnar replay data: t = session ms; ch[name][i] aligns with t[i]; track = [lon, lat, t_ms]. */
export const SessionData = z.object({
  id: z.string(),
  t: z.array(z.number()),
  utc: z.array(z.number().nullable()),
  ch: z.record(z.string(), z.array(z.number().nullable())),
  track: z.array(z.tuple([z.number(), z.number(), z.number()])),
  decimated: z.boolean(),
  /** Text channels aligned with t (faults joined with "; ", module). */
  text: z.record(z.string(), z.array(z.string().nullable())).optional(),
});
export type SessionData = z.infer<typeof SessionData>;

/* ---- replay / notes / audio / accel (ADR-0010, specs/2026-10-05-replay-notes-capture-design.md) ---- */

/** One line of events.jsonl: {t (session ms), type, ...fields}. Open: unknown types are kept. */
export const SessionEvent = z.looseObject({ t: z.number(), type: z.string() });
export type SessionEvent = z.infer<typeof SessionEvent>;
export const SessionEvents = z.object({ id: z.string(), events: z.array(SessionEvent) });

export const CaptureValue = z.object({ module: z.string(), lid: z.string(), raw: z.string(), value: z.string() });
export const Note = z.object({
  id: z.string(),
  t: z.number(),
  t_end: z.number().nullable().optional(),
  text: z.string().default(""),
  tags: z.array(z.string()).default([]),
  kind: z.string(), // "mark" | "note" | "capture"
  source: z.string(), // "live" | "retro"
  created: z.string(),
  edited: z.string().nullable().optional(),
  capture: CaptureValue.nullable().optional(),
});
export type Note = z.infer<typeof Note>;
export const NoteList = z.object({ id: z.string(), notes: z.array(Note) });
export const NoteReply = z.looseObject({ ok: z.boolean().optional(), error: z.string().optional(), note: Note.optional(), session: z.string().optional() });

export const AudioTrack = z.object({
  track: z.string(),
  mime: z.string(),
  start_ms: z.number(),
  end_ms: z.number().nullable().optional(),
  source: z.string(), // "phone" | "pi"
  bytes: z.number().default(0),
});
export type AudioTrack = z.infer<typeof AudioTrack>;

export const AccelCal = z.object({
  matrix: z.array(z.array(z.number())), // 3x3, phone/sensor frame -> vehicle frame
  source: z.string(), // "phone" | "imu"
  method: z.string(), // "level" | "level+gps" | "manual"
});
export type AccelCal = z.infer<typeof AccelCal>;

/** What can be recorded right now (snapshot). Each source: available | unavailable | on, with a reason when unavailable. */
export const SourceState = z.object({ state: z.string(), reason: z.string().nullable().optional() });
export const RecordingSources = z.object({
  gps: z.string(), // "usb" | "mock" | "none"
  pi_audio: SourceState,
  imu: SourceState,
  accel_hz: z.number(),
});
export type RecordingSources = z.infer<typeof RecordingSources>;

export const CaptureList = z.object({
  captures: z.array(CaptureValue.extend({ t: z.number().nullable().optional(), session: z.string().nullable().optional() })),
});

/** GET /pack — the active vehicle pack's manifest (Phase 0, ADR-0013). Module ids are
 * canonical (the signal-store ids); `aliases` maps legacy ids onto them. `layout` is the
 * pack's screen layout (what goes where); every part is optional so a minimal pack works. */
export const PackModule = z.object({
  id: z.string(),
  name: z.string(),
  aliases: z.array(z.string()),
  live: z.boolean(),
});
export const DriveTile = z.object({
  signal: z.string(),
  label: z.string(),
  gauge: z.boolean().optional(),
  dec: z.number().optional(),
  unit: z.string().optional(),
  /** Display = value × scale (e.g. 0.1 turns L/100km into L/mil). */
  scale: z.number().optional(),
});
export type DriveTile = z.infer<typeof DriveTile>;
/** A module's Drive view: "tiles" is generic; any other kind is a pack-registered view. */
export const DriveView = z.looseObject({
  kind: z.string(),
  /** Lead with the HealthStrip. */
  health: z.boolean().optional(),
  tiles: z.array(DriveTile).optional(),
});
export type DriveView = z.infer<typeof DriveView>;
export const BodyRow = z.object({
  signal: z.string(),
  label: z.string(),
  kind: z.enum(["flag", "num"]),
  unit: z.string().optional(),
  dec: z.number().optional(),
});
export type BodyRow = z.infer<typeof BodyRow>;
export const BodyGroup = z.object({ title: z.string(), items: z.array(BodyRow) });
export type BodyGroup = z.infer<typeof BodyGroup>;
export const ModuleNotices = z.looseObject({
  /** Asked before starting a CSV log on this module. */
  record_confirm: z.string().optional(),
  /** Shown above the Inputs list on this module. */
  inputs_banner: z.string().optional(),
});
export const PackLayout = z.looseObject({
  group_order: z.array(z.string()).optional(),
  drive: z.record(z.string(), DriveView).optional(),
  body: z.object({ signals: z.record(z.string(), z.string()), groups: z.array(BodyGroup) }).optional(),
  util_lids: z.record(z.string(), z.object({ example: z.string(), note: z.string() })).optional(),
  notices: z.record(z.string(), ModuleNotices).optional(),
  replay: z.looseObject({ group_categories: z.record(z.string(), z.string()).optional() }).optional(),
});
export type PackLayout = z.infer<typeof PackLayout>;
export const PackSchema = z.object({
  id: z.string(),
  name: z.string(),
  api_version: z.number(),
  default_module: z.string(),
  modules: z.array(PackModule),
  aliases: z.record(z.string(), z.string()),
  layout: PackLayout.default({}),
});
export type Pack = z.infer<typeof PackSchema>;
