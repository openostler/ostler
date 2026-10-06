// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

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

/** One live value in a snapshot: v value, u unit, s range status, c confidence. A node
 * source (NodeSource spec §6.3, §6.4) adds where it came from and how old it is. */
export const SignalValue = z.object({
  v: z.number().nullable(),
  u: z.string().default(""),
  s: z.string().nullable().optional(), // "ok" | "low" | "high" | "suspect" | null
  c: Confidence.optional(),
  /** Node source: the COVESA VSS path it was published under. */
  m: z.string().optional(),
  m_unknown: z.boolean().optional(),
  /** Node source: the field's enumeration label ("closed"). */
  label: z.string().optional(),
  raw: z.number().optional(),
  /** Node source: RFC 3339 UTC when the node read it (null before SNTP). */
  ts_utc: z.string().nullable().optional(),
  /** Node source: seconds since the node read it; null = unknown. */
  age_s: z.number().nullable().optional(),
  /** Node source: a last known value, never shown as live. */
  stale: z.boolean().optional(),
  src: z.string().optional(),
  before_restart: z.boolean().optional(),
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
  /** @deprecated epoch seconds; use since_utc (removed in API 0.2.0) */
  since: z.number().optional(),
  /** RFC 3339 UTC: when the test was started. */
  since_utc: z.string(),
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
  /** @deprecated epoch seconds; use since_utc (removed in API 0.2.0) */
  since: z.number().optional(),
  /** RFC 3339 UTC: when the session started. */
  since_utc: z.string(),
  rows: z.number(),
  /** "recording" while connected; "paused" while the car is disconnected (no rows written). */
  state: z.string().optional(), // absent = "recording" (older servers)
});
export type Recording = z.infer<typeof Recording>;

/** The active K-line link: its profile, how it was found and the ECU's key bytes. */
export const KLineLink = z.object({
  bus: z.string(), // "kline"
  profile: z.string(), // "kwp2000_fast" | "kwp2000_slow" | "iso9141_2" | a pack module id
  protocol: z.string(), // "kwp2000" | "iso9141_2"
  init: z.string(), // "fast" | "5baud" | "none"
  origin: z.string(), // "pack" | "detected" | "remembered" | "override"
  address: z.string(), // "0x33"
  key_bytes: z.string().nullable(), // "E9 8F"
  timing: z.string().nullable(), // "normal" | "extended"; null for ISO 9141-2
  since: z.number().nullable(), // epoch seconds the link came up
});
export type KLineLink = z.infer<typeof KLineLink>;

/** A node's ADR-0040 power record. */
export const NodePower = z.object({
  state: z.string(), // "awake" | "held" | "waking" | "asleep" | "shutting_down"
  since: z.string().nullable().optional(),
  since_us: z.number().optional(),
  class: z.string().optional(),
  next_checkin: z.string().nullable().optional(),
  est_ma: z.number().nullable().optional(),
  reason: z.string().optional(),
});

/** The node that serves the active module (a node source only). */
export const NodeState = z.object({
  device: z.string().nullable(),
  status: z.string().nullable(), // "online" | "offline" | null
  power: NodePower.nullable(),
  boot: z.number().nullable().optional(),
  last_seen_utc: z.string().nullable(),
  broker: z.object({ connected: z.boolean(), host: z.string() }),
  tap: z.null().optional(),
});
export type NodeState = z.infer<typeof NodeState>;

/** One VSS path from the nodes, with the selected source's value on top. */
export const VssReading = z.object({
  sel: z.string(),
  value: z.number().nullable(),
  unit: z.string(),
  ts_utc: z.string().nullable().optional(),
  age_s: z.number().nullable().optional(),
  stale: z.boolean(),
  c: Confidence.optional(),
  sources: z.record(z.string(), z.object({ v: z.number().nullable(), stale: z.boolean() }).passthrough()),
});

/** The snapshot pushed over /events every poll (and returned by /snapshot). */
export const Snapshot = z.object({
  status: z.string(), // "connected" | "connecting" | "error" | "no-cable" | "needs-detect" | "asleep" | "broker-down"
  source: z.string().optional(),
  /** "serial" | "kline" | "node" (NodeSource reads the node's MQTT messages). */
  source_kind: z.string().optional(),
  node: NodeState.nullable().optional(),
  vss: z.record(z.string(), VssReading).optional(),
  devices: z.array(z.string()).optional(),
  faults_note: z.string().optional(),
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
  /** @deprecated server epoch seconds of this snapshot; use ts_utc (removed in API 0.2.0) */
  ts: z.number().optional(),
  /** RFC 3339 UTC instant of this snapshot. */
  ts_utc: z.string(),
  /** Car battery in volts, or null when unknown. */
  battery_v: z.number().nullable().optional(),
  port: PortInfo.optional(),
  /** A latched test that is still on (ActiveTestBanner), else null. */
  active_test: ActiveTest.nullable().optional(),
  gps: GpsFix.nullable().optional(),
  recording: Recording.nullable().optional(),
  recording_sources: z.lazy(() => RecordingSources).nullable().optional(),
  /** The K-line link of the active source (null: no K-line link to report). */
  link: KLineLink.nullable().optional(),
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

/**
 * The error envelope of every API error (4xx/5xx): `error` is for people, `code` a stable
 * token for programs (`not_found`, `public_mode`, `car_refused` …). Open: unknown codes and
 * extra fields are kept.
 */
export const ErrorReply = z.looseObject({
  ok: z.literal(false),
  error: z.string(),
  code: z.string().optional(),
});
export type ErrorReply = z.infer<typeof ErrorReply>;

/** Every /command reply: {ok, message|error} plus action-specific extras. */
export const CommandReply = z.looseObject({
  ok: z.boolean(),
  message: z.string().optional(),
  error: z.string().optional(),
  code: z.string().optional(),
  file: z.string().optional(),
  path: z.string().optional(),
  rows: z.number().optional(),
  fault_watch: z.boolean().optional(),
  mode: z.string().nullable().optional(),
  module: z.string().optional(),
  raws: z.record(z.string(), z.string()).optional(),
  report: z.array(FaultScanEntry).optional(),
  shutting_down: z.boolean().optional(),
  /** detect_protocol: how detection ended (ok | bus-busy | ecu-refused | init-failed | no-ecu). */
  outcome: z.string().optional(),
  /** detect_protocol: the detected K-line link. */
  link: KLineLink.nullable().optional(),
  /** module_scan: one row per probed address. */
  scan: z.array(z.looseObject({ address: z.string(), init: z.string(), module: z.string(), status: z.string() })).optional(),
});
export type CommandReply = z.infer<typeof CommandReply>;

export const AutomapReply = z.looseObject({
  ok: z.boolean(),
  error: z.string().optional(),
  code: z.string().optional(),
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
  error: z.string().nullable().optional(),
  code: z.string().optional(),
  stored: z.boolean().optional(),
  module: z.string().optional(),
  name: z.string().optional(),
  consent: z.boolean().optional(),
  /** a community contribution accepted while offline (HTTP 202, `ok` is true) */
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
  vid: z.string().optional(), // the vehicle id (U0); a legacy session reads as the local vid
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

/** A GeoJSON (RFC 7946) LineString Feature: [lon, lat] positions, properties.t_ms = session ms each. */
export const GeoJsonTrace = z.looseObject({
  type: z.literal("Feature"),
  geometry: z.looseObject({
    type: z.literal("LineString"),
    coordinates: z.array(z.tuple([z.number(), z.number()])),
  }),
  properties: z.looseObject({ t_ms: z.array(z.number()) }),
});
export type GeoJsonTrace = z.infer<typeof GeoJsonTrace>;

/** Columnar replay data: t = session ms; ch[name][i] aligns with t[i]; trace = the GPS track. */
export const SessionData = z.object({
  id: z.string(),
  t: z.array(z.number()),
  /** @deprecated epoch ms per sample; use t0_utc + t (removed in API 0.2.0) */
  utc: z.array(z.number().nullable()).optional(),
  /** RFC 3339 UTC instant of session ms 0 (null without a UTC time). */
  t0_utc: z.string().nullable(),
  ch: z.record(z.string(), z.array(z.number().nullable())),
  /** @deprecated [lon, lat, t_ms]; use trace (removed in API 0.2.0) */
  track: z.array(z.tuple([z.number(), z.number(), z.number()])).optional(),
  /** The GPS track as GeoJSON (null below two positions). */
  trace: GeoJsonTrace.nullable(),
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
/** GET /version: what is running (Settings → Version). A commit is null when unknown. */
const VersionPart = z.object({
  name: z.string(),
  version: z.string().nullable(),
  commit: z.string().nullable(),
  source: z.string().nullable(),
});
export const VersionInfo = z.object({
  platform: VersionPart,
  pack: VersionPart.extend({ id: z.string() }),
  built: z.string().nullable(),
  started: z.string(),
});
export type VersionInfo = z.infer<typeof VersionInfo>;
