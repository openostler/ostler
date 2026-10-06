// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { command } from "../api/client";
import { moduleName } from "../layout";
import { connOf, fmtDown, pillFor } from "../lib/connection";
import { useApp } from "../state/app";
import { useNow } from "../state/useNow";
import { Sheet } from "./Sheet";

/** Connection: state and the connect phases, the serial port (auto or an override), and
 * Retry / Connect / Disconnect. The server is always live (ADR-0011: no mock mode). Opens from
 * the pill, by itself as soon as there is no connection (1 s into `reconnecting`), never
 * during a replay, and again 60 s after a dismissal while still down (see
 * state/connection.ts). `downSince` (ms epoch) drives "No connection for 1 m 20 s". */
export function ConnectionSheet({ onClose, downSince = null }: { onClose: () => void; downSince?: number | null }) {
  const { snap, live, linkUp, module, refresh, toast } = useApp();
  const now = useNow(1000);
  const conn = connOf(snap);
  const [dot, word] = pillFor(conn, linkUp);
  const port = snap?.port;
  const pub = !!snap?.public;

  const send = async (action: string, params?: Record<string, unknown>) => {
    try {
      const r = await command(action, params);
      toast(r.ok ? r.message ?? `${action} ok` : r.error ?? `${action} failed`, !r.ok);
    } catch (e) {
      toast((e as Error).message, true);
    }
    refresh();
  };

  const down = conn === "error" || conn === "lost";
  const offline = conn === "disconnected";
  return (
    <Sheet title="Connection" onClose={onClose}>
      <div className={`card ${down ? "bad" : ""}`}>
        <div className="row" style={{ gap: 8 }}>
          <span className={`pdot ${dot}`} />
          <span className="grow" style={{ fontWeight: 700 }}>{moduleName(module)} — {word}</span>
        </div>
        {downSince !== null && conn !== "connected" ? (
          <div className="small muted" style={{ marginTop: 4 }}>No connection for {fmtDown(now - downSince)}</div>
        ) : null}
        {down ? (
          <>
            <div className="small muted pretty" style={{ marginTop: 4 }}>{snap?.error || "The module did not answer."}</div>
            <ul className="small muted" style={{ margin: "8px 0 0", paddingLeft: 18 }}>
              <li>Ignition on, vehicle stationary.</li>
              <li>Check the KKL cable and OBD pin 7.</li>
              <li>SLABS answers best with the engine running.</li>
            </ul>
          </>
        ) : null}
        {!linkUp ? <div className="small muted" style={{ marginTop: 4 }}>The dashboard lost its link to the Pi — retrying.</div> : null}
        <dl className="kv" style={{ marginTop: 10 }}>
          <dt>SOURCE</dt><dd>{snap?.source ?? "—"}</dd>
          <dt>LINE</dt><dd>10 400 baud · 8N1 · half duplex</dd>
        </dl>
        <div className="btn-row" style={{ marginTop: 12 }}>
          {down ? <button className="btn accent" onClick={() => void send("connect")}>Retry</button> : null}
          {offline ? <button className="btn accent" onClick={() => void send("connect")}>Connect</button> : null}
          {!offline && conn !== "error" ? <button className="btn" onClick={() => void send("disconnect")}>Disconnect</button> : null}
        </div>
      </div>

      {live.seq.length ? (
        <section>
          <div className="kicker group-title">Connection sequence</div>
          <div>
            {live.seq.map((s, i) => {
              const last = i === live.seq.length - 1;
              const active = last && !live.seqDone && conn !== "connected";
              const prev = live.seq[i - 1];
              return (
                <div className="seq-row" key={`${s.phase}-${s.t}`}>
                  <span className={`pdot ${s.ok ? "green" : active ? "yellow blink" : ""}`} />
                  <span className={`grow ${s.ok ? "ok" : ""}`}>{s.phase}</span>
                  <span className="small dis">{prev ? `+${Math.round(s.t - prev.t)} ms` : "0 ms"}</span>
                </div>
              );
            })}
          </div>
        </section>
      ) : null}

      {port && !pub ? (
        <section>
          <div className="kicker" style={{ marginBottom: 8 }}>Serial port</div>
          <div className="small muted" style={{ marginBottom: 8 }}>
            {port.spec === "auto" ? "Auto-selected" : "Fixed"}: <span className="mono">{port.resolved ?? "none found"}</span>
          </div>
          <div className="chanwrap" role="radiogroup" aria-label="Serial port">
            {["auto", ...port.candidates.filter((c) => c !== "auto")].map((p) => (
              <button key={p} className={`chan ${port.spec === p ? "on" : ""}`} role="radio" aria-checked={port.spec === p}
                onClick={() => port.spec !== p && void send("set_port", { port: p })}>
                <span className="mono">{p === "auto" ? "Auto" : p}</span>
              </button>
            ))}
          </div>
        </section>
      ) : null}

      <div className="small dis">One session at a time — the K-line is shared. Pick the module in the header.</div>
      <button className="btn accent" onClick={onClose}>Done</button>
    </Sheet>
  );
}
