import { useAction } from "../api/useAction";
import { useApp } from "../state/app";

/** A latched test is still on (snap.active_test): say so on every screen, with Stop. */
export function ActiveTestBanner() {
  const { snap } = useApp();
  const run = useAction();
  const t = snap?.active_test;
  if (!t) return null;
  return (
    <div className="testbanner" role="alert">
      <span className="pdot yellow blink" />
      <span className="grow"><b>{t.label}</b> is running</span>
      <button className="btn danger" onClick={() => void run(t.stop)}>Stop</button>
    </div>
  );
}
