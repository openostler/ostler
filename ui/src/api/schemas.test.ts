// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";
import type { z } from "zod";
import {
  AutomapReply, Catalog, CatalogModules, CaptureList, CommandReply, NoteList, SessionData, SessionEvents, SessionHistogram, PackSchema, VersionInfo, SessionList, SessionMeta, Community, DocsResponse, FaultsResponse, FieldsResponse, MapResponse,
  ErrorReply, OkReply, Snapshot, SniffResponse,
} from "./schemas";

/**
 * Fixtures are real server responses, written and checked by tests/test_ui_contract.py.
 * If a schema here rejects one, the UI and the server disagree about the contract.
 */
const fixtures = import.meta.glob<unknown>("./fixtures/*.json", { eager: true, import: "default" });

const SCHEMA_FOR: Record<string, z.ZodType> = {
  snapshot: Snapshot,
  "snapshot-kline": Snapshot,
  "snapshot-node": Snapshot,
  "fields-td5": FieldsResponse,
  "fields-slabs": FieldsResponse,
  "faults-airbag": FaultsResponse,
  map: MapResponse,
  sniff: SniffResponse,
  docs: DocsResponse,
  community: Community,
  "community-consent": OkReply,
  "community-queued": OkReply,
  "command-ok": CommandReply,
  "command-error": CommandReply,
  "command-not-recording": CommandReply,
  "error-not-found": ErrorReply,
  "csv-start": CommandReply,
  "csv-stop": CommandReply,
  "read-all-faults": CommandReply,
  automap: AutomapReply,
  capture: OkReply,
  "catalog-td5": Catalog,
  "catalog-bcu": Catalog,
  "catalog-modules": CatalogModules,
  sessions: SessionList,
  "session-meta": SessionMeta,
  "session-data": SessionData,
  "session-events": SessionEvents,
  notes: NoteList,
  captures: CaptureList,
  "session-histogram": SessionHistogram,
  pack: PackSchema,
  version: VersionInfo,
};

describe("API contract fixtures", () => {
  const names = Object.keys(fixtures).map((p) => p.replace("./fixtures/", "").replace(".json", ""));

  it("has a schema for every fixture", () => {
    expect(names.filter((n) => !(n in SCHEMA_FOR))).toEqual([]);
    expect(Object.keys(SCHEMA_FOR).filter((n) => !names.includes(n))).toEqual([]);
  });

  it.each(names)("%s parses with its schema", (name) => {
    const result = SCHEMA_FOR[name]!.safeParse(fixtures[`./fixtures/${name}.json`]);
    expect(result.success ? [] : result.error.issues).toEqual([]);
  });

  it("carries presentation metadata for every field", () => {
    const td5 = FieldsResponse.parse(fixtures["./fixtures/fields-td5.json"]);
    expect(td5.fields.every((f) => f.label && f.group)).toBe(true);
  });
});
