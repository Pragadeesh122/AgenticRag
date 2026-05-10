"use client";

const ITEMS = [
  "Document Search",
  "SQL Queries",
  "Live Web Browsing",
  "Autonomous Reasoning",
  "Real-time Streaming",
  "Multi-source Citations",
  "Document Analysis",
  "Database Intelligence",
  "Semantic Retrieval",
  "Cited Answers",
];

export default function MarqueeStrip() {
  const doubled = [...ITEMS, ...ITEMS];
  return (
    <div
      className="w-full overflow-hidden"
      style={{
        borderTop: "1px solid rgba(255,255,255,0.05)",
        borderBottom: "1px solid rgba(255,255,255,0.05)",
        background: "#161618",
      }}
      aria-hidden="true"
    >
      <div className="flex animate-marquee py-3" style={{ width: "max-content" }}>
        {doubled.map((item, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-4 px-5 shrink-0"
            style={{
              fontSize: "10px",
              fontWeight: 500,
              letterSpacing: "0.15em",
              textTransform: "uppercase",
              color: "rgba(255,255,255,0.2)",
            }}
          >
            {item}
            <span
              className="inline-block w-1 h-1 rounded-full shrink-0"
              style={{ background: "rgba(255,255,255,0.1)" }}
            />
          </span>
        ))}
      </div>
    </div>
  );
}
