import { describe, expect, it } from "vitest";
import bcuFx from "../api/fixtures/catalog-bcu.json";
import modulesFx from "../api/fixtures/catalog-modules.json";
import td5Fx from "../api/fixtures/catalog-td5.json";
import { Catalog, CatalogModules, type CatalogItem } from "../api/schemas";
import {
  actionLocked,
  actionVisible,
  coverageOf,
  coveragePct,
  groupTree,
  identityRows,
  modulesFor,
  pageItems,
  pageOf,
  visible,
  visibleGroups,
} from "./catalog";

const td5 = Catalog.parse(td5Fx);
const bcu = Catalog.parse(bcuFx);
const item = (over: Partial<CatalogItem>): CatalogItem => ({
  id: "x", name: "X", status: "verified", safety: "read", ref: "", note: "", placeholder: false, actions: [], ...over,
});

describe("visible", () => {
  it("shows only verified, non-gated items in Stable", () => {
    expect(visible(item({ status: "verified" }), false)).toBe(true);
    for (const status of ["candidate", "sniff", "untranscribed"]) expect(visible(item({ status }), false)).toBe(false);
    expect(visible(item({ status: "verified", safety: "gated" }), false)).toBe(false);
  });
  it("shows all four statuses and gated items in Experimental", () => {
    for (const status of ["verified", "candidate", "sniff", "untranscribed"]) expect(visible(item({ status }), true)).toBe(true);
    expect(visible(item({ status: "sniff", safety: "gated" }), true)).toBe(true);
  });
});

describe("actions", () => {
  const a = { action: "a", label: "A", status: "verified", safety: "actuator", confirm: "none", preconditions: [], ref: "" };
  it("locks gated and planned actions", () => {
    expect(actionLocked(a)).toBe(false);
    expect(actionLocked({ ...a, safety: "gated" })).toBe(true);
    expect(actionLocked({ ...a, status: "planned" })).toBe(true);
  });
  it("hides candidate (experimental) actions in Stable", () => {
    expect(actionVisible(a, false)).toBe(true);
    expect(actionVisible({ ...a, status: "experimental" }, false)).toBe(false);
    expect(actionVisible({ ...a, status: "experimental" }, true)).toBe(true);
    expect(actionVisible({ ...a, status: "planned" }, true)).toBe(true); // shown, locked
  });
});

describe("pages and groups", () => {
  it("filters a page's groups and drops empty ones", () => {
    expect(visibleGroups(pageOf(td5, "outputs"), false)).toEqual([]);
    expect(visibleGroups(pageOf(td5, "outputs"), true).map((g) => g.group.id)).toEqual(["outputs-tests"]);
    const stable = pageItems(pageOf(td5, "inputs"), false);
    expect(stable.length).toBeGreaterThan(0);
    expect(stable.every((i) => i.status === "verified")).toBe(true);
  });
  it("nests Utilities sub-menus under their parent, two levels", () => {
    const tree = groupTree(pageOf(bcu, "utilities"), true);
    expect(tree.map((t) => t.group.id)).toEqual(["utilities-eka", "utilities-keys"]);
    expect(tree[1]?.children.map((c) => c.group.id))
      .toEqual(["utilities-key-codes", "utilities-key-detect", "utilities-plip"]);
    expect(groupTree(pageOf(bcu, "utilities"), false)).toEqual([]); // gated key programming hidden in Stable
  });
});

describe("coverage", () => {
  it("counts statuses and the verified share", () => {
    const c = coverageOf([{ status: "verified" }, { status: "candidate" }, { status: "sniff" }, { status: "untranscribed" }]);
    expect(c).toEqual({ verified: 1, candidate: 1, sniff: 1, untranscribed: 1, total: 4 });
    expect(coveragePct(c)).toBe(25);
    expect(coveragePct(coverageOf([]))).toBe(0);
  });
  it("lists only modules with something verified in Stable", () => {
    const mods = CatalogModules.parse(modulesFx).modules;
    expect(modulesFor(mods, true).map((m) => m.module))
      .toEqual(["td5", "slabs", "bcu", "ace", "autobox", "airbag"]);
    expect(modulesFor(mods, false).map((m) => m.module)).toEqual(["td5", "slabs"]);
    expect(modulesFor(mods, false, "bcu").map((m) => m.module)).toEqual(["td5", "slabs", "bcu"]);
  });
});

describe("identityRows", () => {
  it("never shows an unmasked VIN", () => {
    expect(identityRows({ part_no: "NNN500", vin: "SALLTGM", VIN_raw: "x", vin_masked: "SALLT****1234" })).toEqual([
      ["part_no", "NNN500"], ["vin_masked", "SALLT****1234"],
    ]);
    expect(identityRows(null)).toEqual([]);
  });
});
