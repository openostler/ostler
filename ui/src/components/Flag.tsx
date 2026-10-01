import type { Flag as FlagT } from "../lib/format";

export function Flag({ flag, dim }: { flag: FlagT; dim?: boolean }) {
  return <span className={`flag ${dim ? "exp" : flag.cls}`}>{dim ? "EXP" : flag.txt}</span>;
}
