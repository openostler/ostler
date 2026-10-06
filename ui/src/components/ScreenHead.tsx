// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { ReactNode } from "react";
import { moduleName } from "../layout";
import { useApp } from "../state/app";

/** Screen title with the active module, and optional controls on the right. */
export function ScreenHead({ title, children }: { title: string; children?: ReactNode }) {
  const { module } = useApp();
  return (
    <div className="screen-head">
      <h2>{title}</h2>
      <span className="sub">· {moduleName(module)}</span>
      {children ? <div className="end">{children}</div> : null}
    </div>
  );
}
