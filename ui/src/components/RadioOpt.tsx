export function RadioOpt({ name, desc, on, onSelect }: {
  name: string; desc: string; on: boolean; onSelect: () => void;
}) {
  return (
    <button className="opt" role="radio" aria-checked={on} onClick={onSelect}>
      <span className="rr"><i /></span>
      <div style={{ minWidth: 0 }}>
        <div className="on-name">{name}</div>
        <div className="on-desc">{desc}</div>
      </div>
    </button>
  );
}
