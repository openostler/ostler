import { describe, expect, it } from "vitest";
import type { z } from "zod";
import {
  AutomapReply, Catalog, CatalogModules, CommandReply, SessionData, SessionList, SessionMeta, Community, DocsResponse, FaultsResponse, FieldsResponse, MapResponse,
  OkReply, Snapshot, SniffResponse,
} from "./schemas";

/**
 * Fixtures are real server responses, written and checked by tests/test_ui_contract.py.
 * If a schema here rejects one, the UI and the server disagree about the contract.
 */
const fixtures = import.meta.glob<unknown>("./fixtures/*.json", { eager: true, import: "default" });

const SCHEMA_FOR: Record<string, z.ZodType> = {
  snapshot: Snapshot,
  "fields-motor": FieldsResponse,
  "fields-slabs": FieldsResponse,
  "faults-airbag": FaultsResponse,
  map: MapResponse,
  sniff: SniffResponse,
  docs: DocsResponse,
  community: Community,
  "community-consent": OkReply,
  "command-ok": CommandReply,
  "command-error": CommandReply,
  "csv-start": CommandReply,
  "csv-stop": CommandReply,
  "read-all-faults": CommandReply,
  automap: AutomapReply,
  capture: OkReply,
  "catalog-motor": Catalog,
  "catalog-bcu": Catalog,
  "catalog-modules": CatalogModules,
  sessions: SessionList,
  "session-meta": SessionMeta,
  "session-data": SessionData,
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
    const motor = FieldsResponse.parse(fixtures["./fixtures/fields-motor.json"]);
    expect(motor.fields.every((f) => f.label && f.group)).toBe(true);
  });
});
