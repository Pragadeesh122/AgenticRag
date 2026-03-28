"use client";

interface RadarChartProps {
  data: Record<string, string | number>[];
  series: string[];
  title?: string;
}

const COLORS = ["#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#f43f5e", "#06b6d4"];

export default function RadarChart({ data, series, title }: RadarChartProps) {
  const n = series.length;
  if (n < 3) return null;

  const cx = 150;
  const cy = 150;
  const R = 110;
  const rings = 4;

  // Find max value across all series for scaling
  let maxVal = 0;
  for (const d of data) {
    for (const s of series) {
      const v = Number(d[s]) || 0;
      if (v > maxVal) maxVal = v;
    }
  }
  if (maxVal === 0) maxVal = 1;

  // Compute vertex positions for a regular polygon
  const angleStep = (2 * Math.PI) / n;
  const vertexAt = (i: number, r: number) => ({
    x: cx + r * Math.cos(angleStep * i - Math.PI / 2),
    y: cy + r * Math.sin(angleStep * i - Math.PI / 2),
  });

  // Grid rings
  const gridRings = Array.from({ length: rings }, (_, ri) => {
    const r = (R / rings) * (ri + 1);
    const points = series.map((_, i) => {
      const p = vertexAt(i, r);
      return `${p.x},${p.y}`;
    });
    return points.join(" ");
  });

  // Axis lines
  const axes = series.map((_, i) => vertexAt(i, R));

  // Data polygons
  const polygons = data.map((d) => {
    const points = series.map((s, i) => {
      const v = Number(d[s]) || 0;
      const r = (v / maxVal) * R;
      const p = vertexAt(i, r);
      return `${p.x},${p.y}`;
    });
    return points.join(" ");
  });

  // Labels positioned just outside the chart
  const labels = series.map((s, i) => {
    const p = vertexAt(i, R + 20);
    let anchor: "middle" | "end" | "start" = "middle";
    if (p.x < cx - 10) anchor = "end";
    else if (p.x > cx + 10) anchor = "start";
    return { text: s, x: p.x, y: p.y, anchor };
  });

  return (
    <div className="flex flex-col items-center gap-3">
      <svg viewBox="0 0 300 300" className="w-full max-w-[320px]">
        {/* Grid rings */}
        {gridRings.map((points, i) => (
          <polygon
            key={`ring-${i}`}
            points={points}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="1"
          />
        ))}

        {/* Axis lines */}
        {axes.map((p, i) => (
          <line
            key={`axis-${i}`}
            x1={cx}
            y1={cy}
            x2={p.x}
            y2={p.y}
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="1"
          />
        ))}

        {/* Data polygons */}
        {polygons.map((points, i) => (
          <g key={`data-${i}`}>
            <polygon
              points={points}
              fill={COLORS[i % COLORS.length]}
              fillOpacity="0.15"
              stroke={COLORS[i % COLORS.length]}
              strokeWidth="2"
            />
            {/* Dots at vertices */}
            {series.map((s, j) => {
              const v = Number(data[i][s]) || 0;
              const r = (v / maxVal) * R;
              const p = vertexAt(j, r);
              return (
                <circle
                  key={`dot-${i}-${j}`}
                  cx={p.x}
                  cy={p.y}
                  r="3"
                  fill={COLORS[i % COLORS.length]}
                />
              );
            })}
          </g>
        ))}

        {/* Labels */}
        {labels.map((l, i) => (
          <text
            key={`label-${i}`}
            x={l.x}
            y={l.y}
            textAnchor={l.anchor}
            dominantBaseline="middle"
            className="fill-zinc-400 text-[10px]"
          >
            {l.text}
          </text>
        ))}
      </svg>

      {/* Legend */}
      {data.length > 1 && (
        <div className="flex flex-wrap gap-3 justify-center">
          {data.map((d, i) => (
            <div key={String(d.label)} className="flex items-center gap-1.5">
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: COLORS[i % COLORS.length] }}
              />
              <span className="text-xs text-zinc-400">{String(d.label)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
