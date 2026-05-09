"use client";

import { useState, useEffect, useRef, useCallback } from "react";

/* ────────────────────────────────────────────────────
   Animated chat demo — plays a looping sequence:
   1. User message appears
   2. RAG tool call runs → done
   3. Web tool call runs → done
   4. Assistant streams in char-by-char with sources
   5. Pause, then reset and replay
   ──────────────────────────────────────────────────── */

const USER_MSG =
  "What does our Q3 report say about churn, and how does it compare to industry benchmarks?";

const ASSISTANT_MSG =
  'Your Q3 report shows **4.2% monthly churn** \u2014 1.8 points above the industry median of 2.4% for B2B SaaS. The report attributes this to onboarding drop-off in weeks 2\u20133, where **38% of new accounts** never complete setup.';

const TOOLS: { name: string; label: string; detail: string; accent: boolean }[] = [
  { name: "rag_search", label: "rag_search", detail: 'Searching "Q3 churn analysis" across 847 documents\u2026', accent: true },
  { name: "web_search", label: "web_search", detail: "Fetching SaaS churn benchmarks 2024\u2026", accent: false },
];

type Phase =
  | "idle"
  | "user"
  | "tool-0-run"
  | "tool-0-done"
  | "tool-1-run"
  | "tool-1-done"
  | "streaming"
  | "sources"
  | "pause";

export default function AnimatedDemo() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [streamIdx, setStreamIdx] = useState(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const streamRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const mountedRef = useRef(true);

  const clear = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (streamRef.current) clearInterval(streamRef.current);
  }, []);

  // Main sequence driver
  useEffect(() => {
    mountedRef.current = true;
    const delay = (ms: number) =>
      new Promise<void>((resolve) => {
        timerRef.current = setTimeout(() => {
          if (mountedRef.current) resolve();
        }, ms);
      });

    async function run() {
      while (mountedRef.current) {
        setPhase("idle");
        setStreamIdx(0);
        await delay(600);
        setPhase("user");
        await delay(1400);
        setPhase("tool-0-run");
        await delay(1800);
        setPhase("tool-0-done");
        await delay(400);
        setPhase("tool-1-run");
        await delay(1600);
        setPhase("tool-1-done");
        await delay(400);
        // Start streaming
        setPhase("streaming");
        setStreamIdx(0);
        await new Promise<void>((resolve) => {
          let idx = 0;
          streamRef.current = setInterval(() => {
            idx++;
            setStreamIdx(idx);
            if (idx >= ASSISTANT_MSG.length) {
              if (streamRef.current) clearInterval(streamRef.current);
              resolve();
            }
          }, 18);
        });
        await delay(300);
        setPhase("sources");
        await delay(4000);
      }
    }

    run();
    return () => {
      mountedRef.current = false;
      clear();
    };
  }, [clear]);

  const showUser = phase !== "idle";
  const showTool0 = [
    "tool-0-run", "tool-0-done", "tool-1-run", "tool-1-done", "streaming", "sources",
  ].includes(phase);
  const tool0Done = phase !== "tool-0-run" && showTool0;
  const showTool1 = [
    "tool-1-run", "tool-1-done", "streaming", "sources",
  ].includes(phase);
  const tool1Done = phase !== "tool-1-run" && showTool1;
  const showAssistant = ["streaming", "sources"].includes(phase);
  const showSources = phase === "sources";

  // Parse bold markdown in streamed text
  const streamedText = ASSISTANT_MSG.slice(0, streamIdx);
  const renderText = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <span key={i} className="font-semibold" style={{ color: "var(--color-lp-text)" }}>
            {part.slice(2, -2)}
          </span>
        );
      }
      return part;
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 px-5 md:px-7 py-6 space-y-4 overflow-hidden">

        {/* User message */}
        <div
          className="flex justify-end transition-all duration-500"
          style={{
            opacity: showUser ? 1 : 0,
            transform: showUser ? "translateY(0)" : "translateY(8px)",
          }}
        >
          <div
            className="max-w-sm px-4 py-3 rounded-2xl text-sm leading-relaxed"
            style={{
              background: "rgba(16,185,129,0.08)",
              border: "1px solid rgba(16,185,129,0.16)",
              color: "rgba(255,255,255,0.82)",
            }}
          >
            {USER_MSG}
          </div>
        </div>

        {/* Tool calls */}
        {TOOLS.map((tool, i) => {
          const show = i === 0 ? showTool0 : showTool1;
          const done = i === 0 ? tool0Done : tool1Done;
          return (
            <div
              key={tool.name}
              className="transition-all duration-[400ms]"
              style={{
                opacity: show ? 1 : 0,
                transform: show ? "translateY(0)" : "translateY(8px)",
                maxWidth: "520px",
              }}
            >
              <div
                className="flex items-start gap-3 px-4 py-3.5 rounded-xl"
                style={{
                  background: "var(--color-lp-surface)",
                  border: "1px solid var(--color-lp-border)",
                  borderLeft: tool.accent ? "2px solid rgba(16,185,129,0.4)" : undefined,
                }}
              >
                <div
                  className="mt-0.5 w-6 h-6 rounded-lg flex items-center justify-center shrink-0"
                  style={{
                    background: tool.accent ? "rgba(16,185,129,0.12)" : "rgba(255,255,255,0.06)",
                    border: tool.accent ? "1px solid rgba(16,185,129,0.18)" : "1px solid rgba(255,255,255,0.1)",
                  }}
                >
                  {/* Icon — magnifying glass for RAG, globe for web */}
                  {tool.accent ? (
                    <svg width="12" height="12" viewBox="0 0 256 256" fill="none">
                      <circle cx="116" cy="116" r="76" stroke="#10b981" strokeWidth="24" />
                      <line x1="172" y1="172" x2="236" y2="236" stroke="#10b981" strokeWidth="24" strokeLinecap="round" />
                    </svg>
                  ) : (
                    <svg width="12" height="12" viewBox="0 0 256 256" fill="none">
                      <circle cx="128" cy="128" r="96" stroke="rgba(255,255,255,0.45)" strokeWidth="20" />
                      <ellipse cx="128" cy="128" rx="96" ry="40" stroke="rgba(255,255,255,0.45)" strokeWidth="20" />
                      <line x1="128" y1="32" x2="128" y2="224" stroke="rgba(255,255,255,0.45)" strokeWidth="20" />
                    </svg>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p
                    className="text-xs font-semibold font-mono"
                    style={{ color: tool.accent ? "#10b981" : "var(--color-lp-text-secondary)" }}
                  >
                    {tool.label}
                  </p>
                  <p className="text-xs mt-0.5 leading-relaxed" style={{ color: "var(--color-lp-text-muted)" }}>
                    {tool.detail}
                  </p>
                </div>
                <div className="ml-auto shrink-0 flex items-center gap-1.5">
                  {done ? (
                    <>
                      <svg width="12" height="12" viewBox="0 0 256 256" fill="none">
                        <circle cx="128" cy="128" r="96" fill="rgba(16,185,129,0.7)" />
                        <polyline points="88,136 112,160 168,104" fill="none" stroke="#fff" strokeWidth="20" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      <span className="text-[10px] font-medium" style={{ color: "rgba(16,185,129,0.6)" }}>
                        Done
                      </span>
                    </>
                  ) : (
                    <div
                      className="w-3 h-3 rounded-full border-2 border-t-transparent"
                      style={{
                        borderColor: "rgba(16,185,129,0.4)",
                        borderTopColor: "transparent",
                        animation: "spin 0.8s linear infinite",
                      }}
                    />
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {/* Assistant response */}
        <div
          className="transition-all duration-[400ms]"
          style={{
            opacity: showAssistant ? 1 : 0,
            transform: showAssistant ? "translateY(0)" : "translateY(8px)",
            maxWidth: "520px",
          }}
        >
          <p
            className="text-[10px] font-semibold tracking-[0.12em] uppercase mb-2"
            style={{ color: "var(--color-lp-text-faint)" }}
          >
            AgenticRAG
          </p>
          <div className="text-sm leading-relaxed" style={{ color: "var(--color-lp-text-secondary)" }}>
            {renderText(streamedText)}
            {phase === "streaming" && (
              <span
                className="inline-block w-0.5 h-3.5 rounded-sm ml-0.5 align-middle"
                style={{
                  background: "#10b981",
                  animation: "blink 1s step-end infinite",
                  opacity: 0.7,
                }}
              />
            )}
          </div>

          {/* Source chips */}
          <div
            className="flex items-center gap-2 mt-3 transition-all duration-500"
            style={{
              opacity: showSources ? 1 : 0,
              transform: showSources ? "translateY(0)" : "translateY(4px)",
            }}
          >
            <div
              className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md"
              style={{
                background: "rgba(16,185,129,0.06)",
                border: "1px solid rgba(16,185,129,0.14)",
              }}
            >
              <span className="w-1 h-1 rounded-full" style={{ background: "#10b981" }} />
              <span className="text-[9px] font-mono" style={{ color: "var(--color-lp-text-muted)" }}>
                Q3 Report.pdf &middot; p.14
              </span>
            </div>
            <div
              className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md"
              style={{
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.06)",
              }}
            >
              <span className="w-1 h-1 rounded-full" style={{ background: "var(--color-lp-text-muted)" }} />
              <span className="text-[9px] font-mono" style={{ color: "var(--color-lp-text-muted)" }}>
                profitwell.com
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Input bar */}
      <div
        className="px-5 md:px-7 py-4"
        style={{ borderTop: "1px solid var(--color-lp-border-subtle)" }}
      >
        <div
          className="flex items-center gap-3 px-4 py-2.5 rounded-xl"
          style={{
            background: "var(--color-lp-surface)",
            border: "1px solid var(--color-lp-border)",
          }}
        >
          <span className="flex-1 text-sm" style={{ color: "var(--color-lp-text-faint)" }}>
            Ask a follow-up question&hellip;
          </span>
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: "rgba(16,185,129,0.15)", border: "1px solid rgba(16,185,129,0.25)" }}
          >
            <svg width="12" height="12" viewBox="0 0 256 256" fill="none">
              <line x1="40" y1="128" x2="216" y2="128" stroke="#10b981" strokeWidth="24" strokeLinecap="round" />
              <polyline points="144,56 216,128 144,200" fill="none" stroke="#10b981" strokeWidth="24" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}
