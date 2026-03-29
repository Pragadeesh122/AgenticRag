"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  TransformWrapper,
  TransformComponent,
  useControls,
  type ReactZoomPanPinchRef,
} from "react-zoom-pan-pinch";

interface MermaidDiagramProps {
  code: string;
  mermaidType?: string;
}

// ── Mermaid singleton: initialize once, render serially ──

let mermaidReady: Promise<typeof import("mermaid")["default"]> | null = null;
let renderQueue: Promise<void> = Promise.resolve();

function getMermaid() {
  if (!mermaidReady) {
    mermaidReady = import("mermaid").then((m) => {
      m.default.initialize({
        startOnLoad: false,
        theme: "base",
        fontFamily: "ui-sans-serif, system-ui, sans-serif",
        fontSize: 14,
        securityLevel: "strict",

        themeVariables: {
          primaryColor: "#27272a",
          primaryTextColor: "#e4e4e7",
          primaryBorderColor: "#3f3f46",
          secondaryColor: "#27272a",
          secondaryTextColor: "#e4e4e7",
          secondaryBorderColor: "#3f3f46",
          tertiaryColor: "#27272a",
          tertiaryTextColor: "#e4e4e7",
          tertiaryBorderColor: "#3f3f46",
          lineColor: "#52525b",
          background: "transparent",
          mainBkg: "#27272a",
          nodeBorder: "#3f3f46",
          clusterBkg: "#1c1c1e",
          clusterBorder: "#3f3f46",
          titleColor: "#e4e4e7",
          edgeLabelBackground: "#18181b",
          nodeTextColor: "#e4e4e7",
          fontSize: "14px",
        },

        flowchart: {
          useMaxWidth: false,
          nodeSpacing: 80,
          rankSpacing: 60,
          padding: 16,
          diagramPadding: 24,
          wrappingWidth: 300,
          htmlLabels: true,
          curve: "basis",
        },
        mindmap: { useMaxWidth: false, padding: 16 },
        sequence: {
          useMaxWidth: false,
          actorFontSize: 14,
          messageFontSize: 14,
          noteFontSize: 12,
          actorMargin: 60,
          messageMargin: 40,
          mirrorActors: false,
        },
        gantt: { useMaxWidth: false },
      });
      return m.default;
    });
  }
  return mermaidReady;
}

/** Queue a mermaid render — only one runs at a time to avoid internal state corruption */
function queueRender(id: string, code: string): Promise<string> {
  const job = renderQueue.then(async () => {
    const mermaid = await getMermaid();
    try {
      const { svg } = await mermaid.render(id, code);
      return svg;
    } finally {
      // Clean up temp DOM elements mermaid creates
      document.getElementById(id)?.remove();
      document.getElementById(`d${id}`)?.remove();
    }
  });
  // Keep queue moving even if this job fails
  renderQueue = job.then(() => {}, () => {});
  return job;
}

// ── Sanitization ──

function fixMindmapIndentation(code: string): string {
  const lines = code.split("\n");
  if (!lines[0]?.trim().startsWith("mindmap")) return code;

  const rootIdx = lines.findIndex((l) => l.trim().startsWith("root"));
  if (rootIdx < 0) return code;

  const contentLines = lines.slice(rootIdx + 1);
  const nonEmpty = contentLines.filter((l) => l.trim());
  if (nonEmpty.length === 0) return code;

  const rootIndent = lines[rootIdx].search(/\S/);
  const allFlat = nonEmpty.every((l) => {
    const indent = l.search(/\S/);
    return indent >= 0 && indent <= rootIndent + 1;
  });
  if (!allFlat) return code;

  const items = nonEmpty.map((l) => l.trim());
  const CHILD = "    ";
  const GCHILD = "      ";

  const isCategory = items.map((text, i) => {
    if (text.split(/\s+/).length !== 1) return false;
    if (/\d/.test(text)) return false;
    const next = items[i + 1];
    return next !== undefined && next.split(/\s+/).length >= 2;
  });

  const result = [lines[0], `  root${lines[rootIdx].trim().replace(/^root/, "")}`];
  let inCategory = false;

  for (let i = 0; i < items.length; i++) {
    let text = items[i];
    if (/[/&'#;:%]/.test(text) && !text.startsWith('"')) {
      text = `"${text}"`;
    }
    if (isCategory[i]) {
      result.push(CHILD + text);
      inCategory = true;
    } else {
      result.push((inCategory ? GCHILD : CHILD) + text);
    }
  }

  return result.join("\n");
}

function sanitizeMermaidCode(code: string): string {
  let sanitized = code
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, '"');
  sanitized = fixMindmapIndentation(sanitized);
  return sanitized;
}

function cleanRenderedSvg(raw: string): string {
  return raw.replace(/style="max-width:[^"]*"/, 'style="width:100%;height:auto;"');
}

// ── Components ──

function ZoomControls({ scale }: { scale: number }) {
  const { zoomIn, zoomOut, resetTransform } = useControls();

  return (
    <div className="absolute bottom-3 right-3 flex items-center gap-1 bg-zinc-800/90 rounded-lg border border-white/10 px-1 py-0.5">
      <button
        onClick={() => zoomOut(0.3)}
        className="px-2 py-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
        title="Zoom out"
      >
        -
      </button>
      <button
        onClick={() => resetTransform()}
        className="px-2 py-1 text-[10px] text-zinc-500 hover:text-zinc-300 transition-colors font-mono min-w-12 text-center"
        title="Reset view"
      >
        {Math.round(scale * 100)}%
      </button>
      <button
        onClick={() => zoomIn(0.3)}
        className="px-2 py-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
        title="Zoom in"
      >
        +
      </button>
    </div>
  );
}

export default function MermaidDiagram({ code }: MermaidDiagramProps) {
  const [svg, setSvg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scale, setScale] = useState(1);
  const renderCount = useRef(0);

  useEffect(() => {
    let cancelled = false;
    const sanitized = sanitizeMermaidCode(code);
    const renderId = `mermaid-${Date.now()}-${++renderCount.current}`;

    queueRender(renderId, sanitized)
      .then((rendered) => {
        if (!cancelled) {
          setSvg(cleanRenderedSvg(rendered));
          setError(null);
        }
      })
      .catch((e) => {
        console.error("[MermaidDiagram] render failed:", e);
        console.error("[MermaidDiagram] code:", sanitized);
        if (!cancelled) {
          setError(String(e));
          setSvg(null);
        }
      });

    return () => { cancelled = true; };
  }, [code]);

  const handleInit = useCallback((ref: ReactZoomPanPinchRef) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        const wrapper = ref.instance.wrapperComponent;
        const content = ref.instance.contentComponent;
        if (!wrapper || !content) return;

        const wW = wrapper.offsetWidth;
        const wH = wrapper.offsetHeight;
        const cW = content.scrollWidth;
        const cH = content.scrollHeight;
        if (cW === 0 || cH === 0) return;

        const fitScale = Math.max(Math.min((wW / cW) * 0.9, (wH / cH) * 0.9, 1), 0.3);
        const x = (wW - cW * fitScale) / 2;
        const y = (wH - cH * fitScale) / 2;

        ref.setTransform(x, y, fitScale, 0);
      });
    });
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

  return (
    <div className="relative">
      <TransformWrapper
        onInit={handleInit}
        onTransformed={(_ref, state) => setScale(state.scale)}
        minScale={0.1}
        maxScale={5}
        limitToBounds={false}
        wheel={{ smoothStep: 0.05 }}
        panning={{ velocityDisabled: true }}
        doubleClick={{ mode: "zoomIn", step: 0.7 }}
      >
        <TransformComponent
          wrapperStyle={{
            width: "100%",
            height: "clamp(300px, 60vh, 700px)",
            borderRadius: "0.5rem",
            background: "rgba(24, 24, 27, 0.5)",
            border: "1px solid rgba(255, 255, 255, 0.05)",
          }}
          contentStyle={{
            width: "fit-content",
            height: "fit-content",
          }}
        >
          <div
            className="[&_svg]:max-w-none [&_svg]:h-auto p-8"
            dangerouslySetInnerHTML={{ __html: svg }}
          />
        </TransformComponent>
        <ZoomControls scale={scale} />
      </TransformWrapper>

      <p className="text-[10px] text-zinc-600 mt-1.5 text-center">
        Scroll to zoom · Drag to pan · Double-click to zoom in
      </p>
    </div>
  );
}
