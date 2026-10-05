import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { PlaybackCtx, usePlaybackState } from "../../state/playback";
import { Transport, type TransportTick } from "./Transport";

const T = Array.from({ length: 301 }, (_, i) => i * 200); // 0 … 60 s

function Harness({ offset = null, onFollow, follow = false, ticks }: {
  offset?: number | null; onFollow?: (on: boolean) => void; follow?: boolean; ticks?: TransportTick[];
}) {
  const pb = usePlaybackState(T);
  return (
    <PlaybackCtx.Provider value={pb}>
      <Transport offset={offset} ticks={ticks} {...(onFollow ? { onFollow, follow } : {})} />
      <output data-testid="time">{Math.round(pb.time)}</output>
    </PlaybackCtx.Provider>
  );
}

const time = () => Number(screen.getByTestId("time").textContent);

describe("Transport", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("play/pause is one toggle with aria-pressed", () => {
    render(<Harness />);
    const play = screen.getByRole("button", { name: "Play" });
    expect(play).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(play);
    expect(play).toHaveAttribute("aria-pressed", "true");
    act(() => { vi.advanceTimersByTime(1000); });
    expect(time()).toBeGreaterThan(800);
    fireEvent.click(play);
    expect(play).toHaveAttribute("aria-pressed", "false");
    const paused = time();
    act(() => { vi.advanceTimersByTime(1000); });
    expect(time()).toBe(paused);
  });

  it("⏪/⏩ jump 10 s and clamp to the session", () => {
    render(<Harness />);
    fireEvent.click(screen.getByRole("button", { name: "Forward 10 seconds" }));
    expect(time()).toBe(10_000);
    fireEvent.click(screen.getByRole("button", { name: "Forward 10 seconds" }));
    fireEvent.click(screen.getByRole("button", { name: "Back 10 seconds" }));
    expect(time()).toBe(10_000);
    fireEvent.click(screen.getByRole("button", { name: "Back 10 seconds" }));
    fireEvent.click(screen.getByRole("button", { name: "Back 10 seconds" }));
    expect(time()).toBe(0);
  });

  it("speed buttons are exclusive and multiply playback", () => {
    render(<Harness />);
    const group = screen.getByRole("group", { name: "Playback speed" });
    expect(group.querySelectorAll("button")).toHaveLength(4);
    expect(screen.getByRole("button", { name: "1×" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "8×" }));
    expect(screen.getByRole("button", { name: "8×" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "1×" })).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    act(() => { vi.advanceTimersByTime(1000); });
    expect(time()).toBeGreaterThan(7000);
  });

  it("the scrubber seeks and shows clock times", () => {
    const start = new Date(2026, 9, 5, 9, 0, 0).getTime();
    render(<Harness offset={start} />);
    const range = screen.getByRole("slider", { name: "Playback position" });
    fireEvent.change(range, { target: { value: "30000" } });
    expect(time()).toBe(30_000);
    expect(range).toHaveAttribute("aria-valuetext", "09:00:30");
    expect(screen.getByTestId("clock-start")).toHaveTextContent("09:00:00");
    expect(screen.getByTestId("clock-end")).toHaveTextContent("09:01:00");
    expect(screen.getByTestId("clock-now")).toHaveTextContent("09:00:30");
  });

  it("without UTC the clocks show session time", () => {
    render(<Harness />);
    expect(screen.getByTestId("clock-start")).toHaveTextContent("0:00");
    expect(screen.getByTestId("clock-end")).toHaveTextContent("1:00");
  });

  it("● Latest appears only when offered, re-pins, and reads pressed while following", () => {
    const { unmount } = render(<Harness />);
    expect(screen.queryByRole("button", { name: "Follow the latest sample" })).toBeNull();
    unmount();
    const onFollow = vi.fn();
    const { rerender } = render(<Harness onFollow={onFollow} />);
    const btn = screen.getByRole("button", { name: "Follow the latest sample" });
    expect(btn).toHaveTextContent("● Latest");
    expect(btn).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(btn);
    expect(onFollow).toHaveBeenCalledWith(true);
    rerender(<Harness onFollow={onFollow} follow />);
    expect(screen.getByRole("button", { name: "Follow the latest sample" })).toHaveAttribute("aria-pressed", "true");
  });

  it("ticks carry a tone word and range ticks are bars; a tap seeks", () => {
    render(<Harness ticks={[
      { id: "n", t: 5_000, label: "Clunk" },
      { id: "w", t: 20_000, t_end: 30_000, label: "Coolant high", tone: "warn" },
      { id: "a", t: 40_000, label: "P0380 Glow plug", tone: "alarm" },
    ]} />);
    const note = screen.getByRole("button", { name: "Note at 0:05: Clunk" });
    const warn = screen.getByRole("button", { name: "Warning at 0:20: Coolant high" });
    const alarm = screen.getByRole("button", { name: "Alarm at 0:40: P0380 Glow plug" });
    expect(note).toHaveClass("tone-note");
    expect(warn).toHaveClass("tone-warn", "range");
    expect(warn.style.width).not.toBe("");
    expect(alarm).toHaveClass("tone-alarm");
    expect(alarm).not.toHaveClass("range");
    fireEvent.click(warn);
    expect(time()).toBe(20_000);
  });
});
