// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { Component, type ReactNode } from "react";

/**
 * An error boundary per destination (app-model spec §5, §9 seam 4): a crash shows "App
 * stopped" in the destination's place and the strip, the nav and the sheets keep working.
 * Keyed by destination by the shell, so moving elsewhere and back retries.
 */
export class Boundary extends Component<{ name: string; children: ReactNode }, { error: Error | null }> {
  state: { error: Error | null } = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error) {
    console.error(`${this.props.name} stopped:`, error);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="card bad" role="alert">
        <div style={{ fontWeight: 700 }}>App stopped</div>
        <div className="small muted pretty">{this.props.name}: {this.state.error.message}</div>
        <button className="btn" style={{ marginTop: 10 }} onClick={() => this.setState({ error: null })}>Try again</button>
      </div>
    );
  }
}
