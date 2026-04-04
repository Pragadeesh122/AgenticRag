"use client";

import RadarChart from "./visualizations/RadarChart";
import LineChart from "./visualizations/LineChart";
import MermaidDiagram from "./visualizations/MermaidDiagram";
import ComparisonTable from "./visualizations/ComparisonTable";

// --- Types ---

interface ChartDataPoint {
  label: string;
  value: number;
  [key: string]: string | number;
}

interface VisualizationData {
  type?: "chart" | "mermaid" | "table";
  title: string;
  description?: string;
  // Numeric chart fields
  chart_type?: string;
  data?: ChartDataPoint[];
  x_label?: string;
  y_label?: string;
  series?: string[];
  // Mermaid fields
  mermaid_type?: string;
  code?: string;
  // Table fields
  headers?: string[];
  rows?: string[][];
}

// --- Parsing ---

function hasChartableData(data: ChartDataPoint[]): boolean {
  return data.length > 0 && data.some((d) => typeof d.value === "number" && d.value > 0);
}

function tryParseVisualization(content: string): VisualizationData | null {
  const tryValidate = (parsed: VisualizationData): VisualizationData | null => {
    if (!parsed.title) return null;

    // Mermaid diagram
    if (parsed.type === "mermaid" && typeof parsed.code === "string" && parsed.code.trim()) {
      return parsed;
    }

    // Comparison table
    if (
      parsed.type === "table" &&
      Array.isArray(parsed.headers) &&
      parsed.headers.length > 0 &&
      Array.isArray(parsed.rows) &&
      parsed.rows.length > 0
    ) {
      return parsed;
    }

    // Numeric chart (type "chart" or absent for backwards compat)
    if (Array.isArray(parsed.data)) {
      // Radar charts don't need a single "value" field
      if (parsed.chart_type === "radar" && parsed.series?.length && parsed.data.length > 0) {
        return { ...parsed, type: "chart" };
      }
      if (hasChartableData(parsed.data)) {
        return { ...parsed, type: parsed.type || "chart" };
      }
    }

    return null;
  };

  // Try raw JSON first
  try {
    return tryValidate(JSON.parse(content.trim()));
  } catch { /* not pure JSON */ }

  // Try extracting JSON from markdown code fence
  const fenceMatch = content.match(/```(?:json)?\s*\n?([\s\S]*?)\n?\s*```/);
  if (fenceMatch) {
    try {
      return tryValidate(JSON.parse(fenceMatch[1].trim()));
    } catch { /* not valid JSON */ }
  }

  // Try extracting a JSON object from content with trailing text
  // (LLM sometimes appends commentary after the JSON)
  const braceStart = content.indexOf("{");
  if (braceStart >= 0) {
    // Find the matching closing brace
    let depth = 0;
    for (let i = braceStart; i < content.length; i++) {
      if (content[i] === "{") depth++;
      else if (content[i] === "}") depth--;
      if (depth === 0) {
        try {
          return tryValidate(JSON.parse(content.slice(braceStart, i + 1)));
        } catch { /* not valid JSON */ }
        break;
      }
    }
  }

  return null;
}

// Keep backwards-compatible export name
const tryParseChart = tryParseVisualization;

// --- Chart Components (bar & pie stay here, they're small) ---

const BAR_COLORS = [
  "bg-violet-500", "bg-blue-500", "bg-emerald-500", "bg-amber-500",
  "bg-rose-500", "bg-cyan-500", "bg-fuchsia-500", "bg-lime-500",
];

function BarChart({ data, xLabel }: { data: ChartDataPoint[]; xLabel?: string }) {
  const maxVal = Math.max(...data.map((d) => d.value), 1);

  return (
    <div className="flex flex-col gap-2">
      {data.map((d, i) => (
        <div key={d.label} className="flex items-center gap-3">
          <span className="text-xs text-zinc-400 w-32 shrink-0 text-right truncate">
            {d.label}
          </span>
          <div className="flex-1 h-7 bg-white/5 rounded-md overflow-hidden relative">
            <div
              className={`h-full ${BAR_COLORS[i % BAR_COLORS.length]} rounded-md transition-all duration-500`}
              style={{ width: `${(d.value / maxVal) * 100}%`, opacity: 0.7 }}
            />
            <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-zinc-300 font-medium">
              {d.value}
            </span>
          </div>
        </div>
      ))}
      {xLabel && (
        <p className="text-xs text-zinc-500 text-center mt-1">{xLabel}</p>
      )}
    </div>
  );
}

function PieChart({ data }: { data: ChartDataPoint[] }) {
  const total = data.reduce((sum, d) => sum + d.value, 0) || 1;
  const pieColors = [
    "#8b5cf6", "#3b82f6", "#10b981", "#f59e0b",
    "#f43f5e", "#06b6d4", "#d946ef", "#84cc16",
  ];

  const { stops } = data.reduce<{ stops: string[]; cumulative: number }>(
    (acc, d, i) => {
      const start = acc.cumulative;
      const pct = (d.value / total) * 100;
      const end = start + pct;
      acc.stops.push(`${pieColors[i % pieColors.length]} ${start}% ${end}%`);
      return { stops: acc.stops, cumulative: end };
    },
    { stops: [], cumulative: 0 }
  );
  const gradient = `conic-gradient(${stops.join(", ")})`;

  return (
    <div className="flex items-start gap-6">
      <div
        className="w-32 h-32 rounded-full shrink-0"
        style={{ background: gradient }}
      />
      <div className="flex flex-col gap-1.5 py-1">
        {data.map((d, i) => (
          <div key={d.label} className="flex items-center gap-2">
            <span
              className="w-2.5 h-2.5 rounded-full shrink-0"
              style={{ backgroundColor: pieColors[i % pieColors.length] }}
            />
            <span className="text-xs text-zinc-300">
              {d.label}{" "}
              <span className="text-zinc-500">
                ({((d.value / total) * 100).toFixed(0)}%)
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Main Renderer ---

export default function ChartRenderer({ content }: { content: string }) {
  const viz = tryParseVisualization(content);
  if (!viz) return null;

  return (
    <div className="flex flex-col gap-3 w-full rounded-xl border border-white/8 bg-white/[0.02] p-4">
      <div>
        <h3 className="text-base font-semibold text-zinc-100">{viz.title}</h3>
        {viz.description && (
          <p className="text-xs text-zinc-500 mt-1">{viz.description}</p>
        )}
      </div>

      {viz.type === "mermaid" ? (
        <MermaidDiagram code={viz.code!} mermaidType={viz.mermaid_type} />
      ) : viz.type === "table" ? (
        <ComparisonTable headers={viz.headers!} rows={viz.rows!} />
      ) : viz.chart_type === "pie" ? (
        <PieChart data={viz.data!} />
      ) : viz.chart_type === "radar" ? (
        <RadarChart data={viz.data!} series={viz.series!} />
      ) : viz.chart_type === "line" ? (
        <LineChart
          data={viz.data!}
          series={viz.series}
          xLabel={viz.x_label}
          yLabel={viz.y_label}
        />
      ) : (
        <BarChart data={viz.data!} xLabel={viz.x_label} />
      )}
    </div>
  );
}

export { tryParseChart };
