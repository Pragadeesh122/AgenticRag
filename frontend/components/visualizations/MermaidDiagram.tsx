"use client";

import { useEffect, useRef, useState, useCallback } from "react";

interface MermaidDiagramProps {
  code: string;
  mermaidType?: string;
}

function sanitizeMermaidCode(code: string): string {
  return code
    .replace(/[\u2018\u2019\u201C\u201D]/g, "'")
    .replace(/\(\(([^)]*)'([^)]*)\)\)/g, "($1$2)")
    .replace(/\[([^\]]*)'([^\]]*)\]/g, "[$1$2]");
}

const MIN_ZOOM = 0.3;
const MAX_ZOOM = 3;

export default function MermaidDiagram({ code }: MermaidDiagramProps) {
  const [svg, setSvg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const idRef = useRef(`mermaid-${Math.random().toString(36).slice(2, 9)}`);

  // Pan & zoom state
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const panStart = useRef({ x: 0, y: 0 });
  const viewportRef = useRef<HTMLDivElement>(null);

  // Render mermaid
  useEffect(() => {
    let cancelled = false;
    const sanitized = sanitizeMermaidCode(code);

    async function render() {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "dark",
          themeVariables: {
            primaryColor: "#7c3aed",
            primaryTextColor: "#d4d4d8",
            primaryBorderColor: "#4c1d95",
            lineColor: "#52525b",
            secondaryColor: "#1e1b4b",
            tertiaryColor: "#18181b",
            background: "transparent",
            mainBkg: "#1c1c1e",
            nodeBorder: "#4c1d95",
            clusterBkg: "rgba(255,255,255,0.02)",
            clusterBorder: "rgba(255,255,255,0.08)",
            titleColor: "#d4d4d8",
            edgeLabelBackground: "#18181b",
            nodeTextColor: "#d4d4d8",
          },
          fontFamily: "ui-monospace, monospace",
          fontSize: 14,
        });

        const { svg: rendered } = await mermaid.render(idRef.current, sanitized);
        if (!cancelled) {
          setSvg(rendered);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(String(e));
          setSvg(null);
        }
      }
    }

    render();
    return () => { cancelled = true; };
  }, [code]);

  // Fit diagram to viewport on first render
  useEffect(() => {
    if (!svg || !viewportRef.current) return;
    const svgEl = viewportRef.current.querySelector("svg");
    if (!svgEl) return;

    const vw = viewportRef.current.clientWidth;
    const vh = viewportRef.current.clientHeight;
    const sw = svgEl.viewBox?.baseVal?.width || svgEl.clientWidth;
    const sh = svgEl.viewBox?.baseVal?.height || svgEl.clientHeight;

    if (sw > 0 && sh > 0) {
      const fitZoom = Math.min(vw / sw, vh / sh, 1);
      setZoom(Math.max(fitZoom, MIN_ZOOM));
      setPan({ x: 0, y: 0 });
    }
  }, [svg]);

  // Wheel zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((z) => Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, z * delta)));
  }, []);

  // Pan handlers
  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    setIsDragging(true);
    dragStart.current = { x: e.clientX, y: e.clientY };
    panStart.current = { ...pan };
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }, [pan]);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!isDragging) return;
    setPan({
      x: panStart.current.x + (e.clientX - dragStart.current.x),
      y: panStart.current.y + (e.clientY - dragStart.current.y),
    });
  }, [isDragging]);

  const handlePointerUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const resetView = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, []);

  if (error) {
    return (
      <pre className="text-xs text-zinc-500 bg-white/[0.02] rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">
        {code}
      </pre>
    );
  }

  if (!svg) {
    return (
      <div className="flex items-center gap-2 py-3">
        <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
        <span className="text-sm text-zinc-400">Rendering diagram...</span>
      </div>
    );
  }

  const zoomPercent = Math.round(zoom * 100);

  return (
    <div className="relative">
      {/* Canvas */}
      <div
        ref={viewportRef}
        className="w-full h-[400px] rounded-lg bg-zinc-900/50 border border-white/5 overflow-hidden select-none"
        style={{ cursor: isDragging ? "grabbing" : "grab" }}
        onWheel={handleWheel}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
      >
        <div
          className="w-full h-full flex items-center justify-center"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: "center center",
            transition: isDragging ? "none" : "transform 0.1s ease-out",
          }}
        >
          <div
            className="[&_svg]:max-w-none [&_svg]:h-auto"
            dangerouslySetInnerHTML={{ __html: svg }}
          />
        </div>
      </div>

      {/* Controls */}
      <div className="absolute bottom-3 right-3 flex items-center gap-1 bg-zinc-800/90 rounded-lg border border-white/10 px-1 py-0.5">
        <button
          onClick={() => setZoom((z) => Math.max(MIN_ZOOM, z * 0.8))}
          className="px-2 py-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
          title="Zoom out"
        >
          -
        </button>
        <button
          onClick={resetView}
          className="px-2 py-1 text-[10px] text-zinc-500 hover:text-zinc-300 transition-colors font-mono min-w-[3rem] text-center"
          title="Reset view"
        >
          {zoomPercent}%
        </button>
        <button
          onClick={() => setZoom((z) => Math.min(MAX_ZOOM, z * 1.2))}
          className="px-2 py-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
          title="Zoom in"
        >
          +
        </button>
      </div>

      {/* Hint */}
      <p className="text-[10px] text-zinc-600 mt-1.5 text-center">
        Scroll to zoom · Drag to pan
      </p>
    </div>
  );
}
