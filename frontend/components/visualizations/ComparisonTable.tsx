"use client";

interface ComparisonTableProps {
  headers: string[];
  rows: string[][];
}

export default function ComparisonTable({ headers, rows }: ComparisonTableProps) {
  if (!headers.length || !rows.length) return null;

  return (
    <div className="w-full overflow-x-auto rounded-lg border border-white/8">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-white/[0.04]">
            {headers.map((h) => (
              <th
                key={h}
                className="px-4 py-2.5 text-left text-xs font-medium text-zinc-300 border-b border-white/8"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className="border-b border-white/5 hover:bg-white/[0.02] transition-colors"
            >
              {row.map((cell, j) => (
                <td
                  key={j}
                  className={`px-4 py-2 ${
                    j === 0 ? "text-zinc-200 font-medium" : "text-zinc-400"
                  }`}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
