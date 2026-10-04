import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { PlaybackCtx, usePlaybackState } from "../../state/playback";
import { Transport } from "./Transport";

const T = Array.from({ length: 301 }, (_, i) => i * 200); // 0 … 60 s

function Harness({ offset = null, onFollow }: { offset?: number | null; onFollow?: (on: boolean) => void }) {
  const pb = usePlaybackState(T);
  return (
    <PlaybackCtx.Provider value={pb}>
      <Transport offset={offset} {...(onFollow ? { onFollow, follow: false } : {})} />
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

  it("Follow live appears only when offered", () => {
    const { unmount } = render(<Harness />);
    expect(screen.queryByRole("button", { name: "Follow live" })).toBeNull();
    unmount();
    const onFollow = vi.fn();
    render(<Harness onFollow={onFollow} />);
    fireEvent.click(screen.getByRole("button", { name: "Follow live" }));
    expect(onFollow).toHaveBeenCalledWith(true);
  });
});
