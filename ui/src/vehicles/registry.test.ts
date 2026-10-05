import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { getPack, setPack, usePack } from "../pack/store";
import { packFixture } from "../test/packFixture";
import { getView, registerViews } from "./registry";

describe("vehicle view registry", () => {
  it("looks views up by pack and kind; unknown ones are undefined", () => {
    const A = () => null;
    const B = () => null;
    registerViews("fake", { a: A });
    registerViews("fake", { b: B }); // extends, does not replace
    expect(getView("fake", "a")).toBe(A);
    expect(getView("fake", "b")).toBe(B);
    expect(getView("fake", "tiles")).toBeUndefined();
    expect(getView("other", "a")).toBeUndefined();
    expect(getView(undefined, "a")).toBeUndefined();
  });

  it("has the real pack's views registered (composition root)", () => {
    for (const view of Object.values(packFixture.layout.drive ?? {})) {
      if (view.kind !== "tiles") expect(getView(packFixture.id, view.kind), view.kind).toBeDefined();
    }
  });
});

describe("pack store", () => {
  it("serves hook and non-hook callers, and re-renders on change", () => {
    const { result } = renderHook(() => usePack());
    expect(result.current).toBe(packFixture);
    act(() => setPack(null));
    expect(getPack()).toBeNull();
    expect(result.current).toBeNull();
    act(() => setPack(packFixture));
    expect(result.current?.default_module).toBe(packFixture.default_module);
  });
});
