import type { ReactNode } from "react";
import { Glossary } from "./Glossary";

const MARKS = ["①", "②", "③", "④", "⑤"];

/** Admin screen header: a title, a one-line purpose, numbered steps and the glossary. */
export function StepHeader({ title, purpose, steps, children }: {
  title: string; purpose: string; steps: ReactNode[]; children?: ReactNode;
}) {
  return (
    <div className="step-header">
      <div className="screen-head">
        <h2>{title}</h2>
        <span className="sub">— {purpose}</span>
        <div className="end"><Glossary /></div>
      </div>
      <ol className="steps" aria-label="How it works">
        {steps.map((s, i) => (
          <li key={i}><span className="step-n" aria-hidden="true">{MARKS[i] ?? `${i + 1}.`}</span><span>{s}</span></li>
        ))}
      </ol>
      {children}
    </div>
  );
}
