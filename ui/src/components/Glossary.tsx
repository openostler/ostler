import { useEffect, useId, useRef, useState } from "react";

/** The words the admin Decode and Label tabs use, in plain English. */
const GLOSSARY: { term: string; text: string }[] = [
  { term: "LID", text: "Local identifier: the number of one data block inside a module (an ECU). Each block holds several values packed as bytes — e.g. block 09 on the Td5 holds engine speed." },
  { term: "21 xx", text: "The request that reads a block (ReadDataByLocalIdentifier). “21 09” asks the module “send me block 09”; it only reads, never changes anything." },
  { term: "Reference tool", text: "The NanoCom: a commercial diagnostic tool that already knows what the bytes mean. We use what it shows on screen as the answer key." },
  { term: "Sniff tap", text: "An ESP32 wired to the K-line (OBD pin 7) that only listens. It records what the NanoCom asks for and what the module answers, without sending anything itself." },
  { term: "Decode / solve", text: "Working out which bytes hold a value and how to turn them into a number: given a few raw readings and the value the NanoCom showed for each, the solver finds the byte offset and scale." },
];

/** ⓘ button that opens a small glossary popover. Escape or a second tap closes it. */
export function Glossary() {
  const [open, setOpen] = useState(false);
  const id = useId();
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    const onDown = (e: PointerEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    window.addEventListener("keydown", onKey);
    window.addEventListener("pointerdown", onDown);
    return () => { window.removeEventListener("keydown", onKey); window.removeEventListener("pointerdown", onDown); };
  }, [open]);
  return (
    <div className="gloss" ref={ref}>
      <button type="button" className="iconbtn gloss-btn" aria-label="Glossary" aria-expanded={open} aria-controls={id}
        onClick={() => setOpen((o) => !o)}>ⓘ<span className="gloss-word">Glossary</span></button>
      {open ? (
        <div className="gloss-pop" id={id} role="region" aria-label="Glossary terms">
          <dl>
            {GLOSSARY.map((g) => (
              <div key={g.term}><dt>{g.term}</dt><dd>{g.text}</dd></div>
            ))}
          </dl>
        </div>
      ) : null}
    </div>
  );
}
