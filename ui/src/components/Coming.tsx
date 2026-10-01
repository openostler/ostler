export function ComingCard({ title, items }: { title: string; items: { name: string; tag: string }[] }) {
  return (
    <div className="card">
      <div className="kicker" style={{ marginBottom: 10 }}>{title}</div>
      <div className="stack">
        {items.map((i) => (
          <div className="comingrow" key={i.name}>
            <span className="pdot" />
            {i.name}
            <span className="tag">{i.tag}</span>
          </div>
        ))}
      </div>
      <div className="small muted pretty" style={{ paddingTop: 10 }}>
        These exist on the module and are sniffed or planned — not yet wired up.
      </div>
    </div>
  );
}
