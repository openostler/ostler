import { describe, expect, it } from "vitest";
import sessionsFx from "../../api/fixtures/sessions.json";
import { SessionList, type SessionMeta } from "../../api/schemas";
import { dayLabel, formatDuration, formatPos, groupByDay, localDay, recordingMinutes, startTime } from "./sessionFormat";

const base = SessionList.parse(sessionsFx).sessions[0]!;
const at = (y: number, mo: number, d: number, h: number, id: string): SessionMeta =>
  ({ ...base, id, start_utc: new Date(y, mo - 1, d, h, 0).toISOString() });

describe("session list grouping", () => {
  const now = new Date(2026, 9, 5, 18, 0);

  it("groups by local day, newest first", () => {
    const g = groupByDay([at(2026, 10, 4, 8, "a"), at(2026, 10, 5, 9, "b"), at(2026, 10, 5, 17, "c"), at(2026, 9, 30, 12, "d")], now);
    expect(g.map((x) => x.day)).toEqual(["2026-10-05", "2026-10-04", "2026-09-30"]);
    expect(g[0]!.label).toBe("Today");
    expect(g[1]!.label).toBe("Yesterday");
    expect(g[2]!.label).not.toMatch(/Today|Yesterday/);
    expect(g[0]!.sessions.map((s) => s.id)).toEqual(["c", "b"]);
  });

  it("empty list → no groups", () => {
    expect(groupByDay([], now)).toEqual([]);
  });

  it("labels and local start time", () => {
    expect(localDay(new Date(2026, 0, 2, 23, 59))).toBe("2026-01-02");
    expect(dayLabel("2026-10-05", now)).toBe("Today");
    expect(startTime(at(2026, 10, 5, 7, "x"))).toBe("07:00");
  });
});

describe("row formatting", () => {
  it("durations", () => {
    expect(formatDuration(42)).toBe("42 s");
    expect(formatDuration(720)).toBe("12 min");
    expect(formatDuration(3900)).toBe("1 h 05 min");
  });

  it("start position rounded to 3 dp as lat, lon, or no GPS", () => {
    expect(formatPos([-1.20049, 52.02051])).toBe("52.021, -1.200");
    expect(formatPos(null)).toBe("no GPS");
  });

  it("recording minutes", () => {
    expect(recordingMinutes(1000, 1000 + 59)).toBe(0);
    expect(recordingMinutes(1000, 1000 + 61 * 7)).toBe(7);
  });
});
