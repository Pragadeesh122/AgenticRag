"use client";

interface LineChartProps {
  data: Record<string, string | number>[];
  series?: string[];
  xLabel?: string;
  yLabel?: string;
}

const COLORS = ["#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#f43f5e", "#06b6d4"];

export default function LineChart({ data, series, xLabel, yLabel }: LineChartProps) {
  if (data.length < 2) return null;

  const keys = series ?? ["value"];
  const pad = { top: 20, right: 20, bottom: 40, left: 50 };
  const w = 500;
  const h = 240;
  const plotW = w - pad.left - pad.right;
  const plotH = h - pad.top - pad.bottom;

  // Find min/max values
  let minVal = Infinity;
  let maxVal = -Infinity;
  for (const d of data) {
    for (const k of keys) {
      const v = Number(d[k]) || 0;
      if (v < minVal) minVal = v;
      if (v > maxVal) maxVal = v;
    }
  }
  if (minVal === maxVal) {
    maxVal = minVal + 1;
    minVal = Math.max(0, minVal - 1);
  }
  // Start from 0 if all values positive
  if (minVal > 0) minVal = 0;

  const range = maxVal - minVal || 1;

  // Point positions
  const xStep = plotW / (data.length - 1);
  const toX = (i: number) => pad.left + i * xStep;
  const toY = (v: number) => pad.top + plotH - ((v - minVal) / range) * plotH;

  // Grid lines (4 horizontal)
  const gridLines = Array.from({ length: 5 }, (_, i) => {
    const v = minVal + (range / 4) * i;
    return { y: toY(v), label: v % 1 === 0 ? String(v) : v.toFixed(1) };
  });

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full">
        {/* Grid */}
        {gridLines.map((g) => (
          <g key={g.label}>
            <line
              x1={pad.left}
              y1={g.y}
              x2={w - pad.right}
              y2={g.y}
              stroke="rgba(255,255,255,0.06)"
              strokeWidth="1"
            />
            <text
              x={pad.left - 8}
              y={g.y}
              textAnchor="end"
              dominantBaseline="middle"
              className="fill-zinc-500 text-[10px]"
            >
              {g.label}
            </text>
          </g>
        ))}

        {/* Lines + areas */}
        {keys.map((k, ki) => {
          const points = data.map((d, i) => ({
            x: toX(i),
            y: toY(Number(d[k]) || 0),
          }));
          const polyline = points.map((p) => `${p.x},${p.y}`).join(" ");
          const areaPath = [
            `M ${points[0].x},${toY(minVal)}`,
            ...points.map((p) => `L ${p.x},${p.y}`),
            `L ${points[points.length - 1].x},${toY(minVal)} Z`,
          ].join(" ");

          return (
            <g key={k}>
              <path d={areaPath} fill={COLORS[ki % COLORS.length]} opacity="0.08" />
              <polyline
                points={polyline}
                fill="none"
                stroke={COLORS[ki % COLORS.length]}
                strokeWidth="2"
                strokeLinejoin="round"
              />
              {points.map((p, i) => (
                <circle
                  key={i}
                  cx={p.x}
                  cy={p.y}
                  r="3"
                  fill={COLORS[ki % COLORS.length]}
                />
              ))}
            </g>
          );
        })}

        {/* X-axis labels */}
        {data.map((d, i) => (
          <text
            key={String(d.label)}
            x={toX(i)}
            y={h - pad.bottom + 16}
            textAnchor="middle"
            className="fill-zinc-500 text-[9px]"
          >
            {String(d.label).length > 12
              ? String(d.label).slice(0, 11) + "…"
              : String(d.label)}
          </text>
        ))}

        {/* Axis labels */}
        {xLabel && (
          <text
            x={pad.left + plotW / 2}
            y={h - 4}
            textAnchor="middle"
            className="fill-zinc-500 text-[10px]"
          >
            {xLabel}
          </text>
        )}
        {yLabel && (
          <text
            x={12}
            y={pad.top + plotH / 2}
            textAnchor="middle"
            dominantBaseline="middle"
            transform={`rotate(-90, 12, ${pad.top + plotH / 2})`}
            className="fill-zinc-500 text-[10px]"
          >
            {yLabel}
          </text>
        )}
      </svg>

      {/* Legend for multi-series */}
      {keys.length > 1 && (
        <div className="flex flex-wrap gap-3 justify-center mt-2">
          {keys.map((k, i) => (
            <div key={k} className="flex items-center gap-1.5">
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: COLORS[i % COLORS.length] }}
              />
              <span className="text-xs text-zinc-400">{k}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
