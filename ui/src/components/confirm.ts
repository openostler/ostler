/**
 * The ONE confirmation for anything that writes to an ECU or drives hardware
 * (actuators, clear faults, shutdown). Kept as a plain function so every caller states
 * the same safety conditions; tests stub window.confirm.
 */
export const SAFETY = "Vehicle stationary, handbrake on, ignition on, nobody under the car.";

export function confirmAction(title: string, detail: string = SAFETY): boolean {
  return window.confirm(`${title}\n\n${detail}`);
}
