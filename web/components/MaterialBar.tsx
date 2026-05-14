import type { TextileDigitalProductPassport } from "@/lib/generated/textile-dpp";

const PALETTE = [
  "bg-chart-1",
  "bg-chart-2",
  "bg-chart-3",
  "bg-chart-4",
  "bg-chart-5",
];

export function MaterialBar({
  materials,
}: {
  materials: TextileDigitalProductPassport["composition"]["materials"];
}) {
  return (
    <div className="space-y-3">
      <div
        role="img"
        aria-label={`Material composition: ${materials.map((m) => `${m.percentage}% ${m.name}`).join(", ")}`}
        className="flex h-3 w-full overflow-hidden rounded-full bg-muted"
      >
        {materials.map((m, i) => (
          <div
            key={m.name}
            className={PALETTE[i % PALETTE.length]}
            style={{ width: `${m.percentage}%` }}
          />
        ))}
      </div>
      <ul className="space-y-1.5 text-sm">
        {materials.map((m, i) => (
          <li key={m.name} className="flex items-center gap-2">
            <span
              aria-hidden
              className={`inline-block h-2.5 w-2.5 rounded-full ${PALETTE[i % PALETTE.length]}`}
            />
            <span className="flex-1">{m.name}</span>
            <span className="font-mono text-muted-foreground">{m.percentage}%</span>
            {m.recycledContentPercentage !== undefined &&
              m.recycledContentPercentage > 0 && (
                <span className="text-xs text-muted-foreground">
                  ({m.recycledContentPercentage}% recycled)
                </span>
              )}
          </li>
        ))}
      </ul>
    </div>
  );
}
