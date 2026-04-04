import Link from "next/link";
import { ArrowRight } from "@phosphor-icons/react/dist/ssr/ArrowRight";
import { ArrowUpRight } from "@phosphor-icons/react/dist/ssr/ArrowUpRight";
import { CheckCircle } from "@phosphor-icons/react/dist/ssr/CheckCircle";
import { Files } from "@phosphor-icons/react/dist/ssr/Files";
import { Database } from "@phosphor-icons/react/dist/ssr/Database";
import { Globe } from "@phosphor-icons/react/dist/ssr/Globe";
import { GitBranch } from "@phosphor-icons/react/dist/ssr/GitBranch";
import { Lightning } from "@phosphor-icons/react/dist/ssr/Lightning";
import AnimatedDemo from "@/components/landing/AnimatedDemo";

export default function LandingPage() {
  return (
    <div
      className="min-h-[100dvh] overflow-x-hidden"
      style={{ background: "#ffffff", color: "#0a0a0a" }}
    >

      {/* ── Navbar ── */}
      <header
        className="sticky top-0 z-40 w-full"
        style={{
          background: "rgba(255,255,255,0.85)",
          backdropFilter: "saturate(180%) blur(20px)",
          WebkitBackdropFilter: "saturate(180%) blur(20px)",
          borderBottom: "1px solid #f0f0f1",
        }}
        role="banner"
      >
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 h-14 flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5" aria-label="AgenticRAG home">
            <div
              className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0"
              style={{
                background: "rgba(16,185,129,0.1)",
                border: "1px solid rgba(16,185,129,0.2)",
              }}
            >
              <div className="w-2 h-2 rounded-full" style={{ background: "#10b981" }} />
            </div>
            <span className="text-[13px] font-bold tracking-tight" style={{ color: "#0a0a0a" }}>
              AgenticRAG
            </span>
          </Link>

          {/* Center nav */}
          <nav className="hidden md:flex items-center gap-1" aria-label="Page navigation">
            {[
              { label: "Features", href: "#capabilities-heading" },
              { label: "How it works", href: "#how-it-works-heading" },
            ].map(({ label, href }) => (
              <a
                key={label}
                href={href}
                className="px-3 py-1.5 text-[13px] rounded-lg transition-colors duration-150"
                style={{ color: "#6b7280" }}
              >
                {label}
              </a>
            ))}
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[13px] rounded-lg transition-colors duration-150"
              style={{ color: "#6b7280" }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
              </svg>
              GitHub
            </a>
          </nav>

          <div className="flex items-center gap-2">
            <Link
              href="/chat"
              className="px-3.5 py-1.5 text-[13px] rounded-full transition-colors duration-150 hidden sm:inline-flex"
              style={{ color: "#6b7280" }}
            >
              Sign in
            </Link>
            <Link
              href="/chat"
              className="lp-btn-primary inline-flex items-center gap-1.5 px-4 py-1.5 text-[13px] font-medium rounded-full text-white"
            >
              Get started
              <ArrowRight size={11} weight="bold" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </header>

      <main>

        {/* ── Hero ── */}
        <section className="relative overflow-hidden" aria-labelledby="hero-heading">

          {/* Subtle dot grid */}
          <div
            className="pointer-events-none absolute inset-0"
            aria-hidden="true"
            style={{
              backgroundImage: "radial-gradient(#d1d5db 0.8px, transparent 0.8px)",
              backgroundSize: "24px 24px",
              maskImage: "radial-gradient(ellipse 70% 50% at 50% 30%, black 10%, transparent 70%)",
              WebkitMaskImage: "radial-gradient(ellipse 70% 50% at 50% 30%, black 10%, transparent 70%)",
            }}
          />

          {/* Content */}
          <div className="relative max-w-[1400px] mx-auto px-6 md:px-10 pt-20 md:pt-28 pb-8">

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16 items-start">

              {/* Left — copy + CTA */}
              <div className="lg:col-span-5 relative z-10 pt-4 md:pt-8">

                {/* Small open-source tag */}
                <div className="flex items-center gap-2 mb-8">
                  <span
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium"
                    style={{
                      background: "rgba(16,185,129,0.08)",
                      color: "#059669",
                      border: "1px solid rgba(16,185,129,0.15)",
                    }}
                  >
                    <span className="w-1 h-1 rounded-full" style={{ background: "#10b981" }} aria-hidden="true" />
                    Open source
                  </span>
                </div>

                {/* Headline */}
                <h1
                  id="hero-heading"
                  className="mb-6"
                  style={{
                    fontFamily: "var(--font-geist-sans), system-ui, sans-serif",
                    fontStyle: "normal",
                    fontSize: "clamp(2.5rem, 5vw, 3.75rem)",
                    fontWeight: 700,
                    lineHeight: 1.08,
                    letterSpacing: "-0.04em",
                    color: "#0a0a0a",
                  }}
                >
                  Your data already
                  <br />
                  has the answers.
                </h1>

                {/* Subtitle */}
                <p
                  className="leading-relaxed mb-10"
                  style={{
                    maxWidth: "400px",
                    fontSize: "1.0625rem",
                    lineHeight: 1.6,
                    color: "#525252",
                  }}
                >
                  Drop your files, connect a database, point at the web.
                  AgenticRAG searches across all of it and cites every source.
                </p>

                <div className="flex flex-col sm:flex-row items-start gap-3 mb-16 lg:mb-0">
                  <Link
                    href="/chat"
                    className="lp-btn-primary inline-flex items-center gap-2 px-6 py-3 text-sm font-semibold rounded-full text-white"
                    style={{
                      boxShadow: "0 1px 2px rgba(0,0,0,0.1), 0 4px 12px rgba(0,0,0,0.1)",
                    }}
                  >
                    Start for free
                    <ArrowRight size={14} weight="bold" aria-hidden="true" />
                  </Link>
                  <Link
                    href="/chat"
                    className="lp-btn-ghost inline-flex items-center gap-2 px-6 py-3 text-sm font-medium rounded-full"
                  >
                    Sign in
                  </Link>
                </div>
              </div>

              {/* Right — dark demo window (contrast piece) */}
              <div className="lg:col-span-7 relative">

                {/* Shadow wash behind */}
                <div
                  className="pointer-events-none absolute -inset-8"
                  aria-hidden="true"
                  style={{
                    background: "radial-gradient(ellipse 80% 70% at 50% 50%, rgba(0,0,0,0.04), transparent)",
                  }}
                />

                {/* Dark app window */}
                <div
                  className="relative overflow-hidden"
                  style={{
                    borderRadius: "16px",
                    border: "1px solid rgba(0,0,0,0.12)",
                    background: "#0a0a0a",
                    boxShadow: `
                      0 24px 80px -12px rgba(0,0,0,0.25),
                      0 8px 24px -8px rgba(0,0,0,0.15),
                      0 0 0 1px rgba(255,255,255,0.06) inset
                    `,
                  }}
                >
                  {/* Titlebar */}
                  <div
                    className="flex items-center gap-3 px-5 py-3"
                    style={{
                      borderBottom: "1px solid rgba(255,255,255,0.06)",
                      background: "rgba(255,255,255,0.015)",
                    }}
                    aria-hidden="true"
                  >
                    <div className="flex items-center gap-1.5">
                      <div className="w-[10px] h-[10px] rounded-full" style={{ background: "#ff5f57" }} />
                      <div className="w-[10px] h-[10px] rounded-full" style={{ background: "#ffbd2e" }} />
                      <div className="w-[10px] h-[10px] rounded-full" style={{ background: "#28c840" }} />
                    </div>
                    <div
                      className="flex-1 mx-6 h-6 rounded-md flex items-center justify-center gap-2"
                      style={{ background: "rgba(255,255,255,0.04)", maxWidth: "300px", margin: "0 auto" }}
                    >
                      <span className="w-1.5 h-1.5 rounded-full" style={{ background: "rgba(16,185,129,0.5)" }} />
                      <span className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.25)" }}>
                        agenticrag.app
                      </span>
                    </div>
                  </div>

                  {/* App body */}
                  <div className="flex" style={{ minHeight: "400px", maxHeight: "480px" }}>

                    {/* Sidebar */}
                    <div
                      className="w-44 shrink-0 p-3 hidden lg:flex flex-col gap-0.5"
                      style={{
                        borderRight: "1px solid rgba(255,255,255,0.05)",
                        background: "rgba(0,0,0,0.25)",
                      }}
                      aria-hidden="true"
                    >
                      <div className="flex items-center gap-2 px-2 py-2 mb-2">
                        <span className="w-1.5 h-1.5 rounded-full" style={{ background: "rgba(16,185,129,0.5)" }} />
                        <span className="text-[10px] font-semibold" style={{ color: "rgba(255,255,255,0.35)" }}>AgenticRAG</span>
                      </div>
                      <div
                        className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg mb-3"
                        style={{ background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.15)" }}
                      >
                        <span className="text-[10px] font-medium" style={{ color: "rgba(16,185,129,0.8)" }}>+ New chat</span>
                      </div>
                      {[
                        { label: "Q3 churn analysis", active: true },
                        { label: "Revenue forecast" },
                        { label: "Competitor pricing" },
                      ].map(({ label, active }) => (
                        <div
                          key={label}
                          className="flex items-center px-2.5 py-1.5 rounded-md"
                          style={{
                            background: active ? "rgba(255,255,255,0.05)" : "transparent",
                            borderLeft: active ? "2px solid rgba(16,185,129,0.5)" : "2px solid transparent",
                          }}
                        >
                          <span
                            className="text-[10px] truncate"
                            style={{ color: active ? "rgba(255,255,255,0.7)" : "rgba(255,255,255,0.25)" }}
                          >
                            {label}
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* Animated chat */}
                    <div className="flex-1 flex flex-col min-w-0">
                      <AnimatedDemo />
                    </div>
                  </div>
                </div>

                {/* Bottom fade to white */}
                <div
                  className="pointer-events-none absolute bottom-0 left-0 right-0 h-16"
                  aria-hidden="true"
                  style={{ background: "linear-gradient(to bottom, transparent, #ffffff)" }}
                />
              </div>
            </div>
          </div>
        </section>

        {/* ── Capabilities ── */}
        <section
          className="relative px-6 md:px-10 pt-24 pb-20"
          style={{ maxWidth: "1400px", margin: "0 auto" }}
          aria-labelledby="capabilities-heading"
        >
          <div className="flex items-center gap-3 mb-5">
            <p className="text-xs font-semibold tracking-[0.18em] uppercase shrink-0" style={{ color: "#10b981" }}>
              Capabilities
            </p>
            <span className="flex-1 h-px" style={{ background: "#f0f0f1" }} aria-hidden="true" />
          </div>

          <h2
            id="capabilities-heading"
            className="mb-14"
            style={{
              fontFamily: "var(--font-geist-sans), system-ui, sans-serif",
              fontStyle: "normal",
              fontWeight: 700,
              fontSize: "clamp(1.75rem, 3.5vw, 2.5rem)",
              letterSpacing: "-0.035em",
              color: "#0a0a0a",
              lineHeight: 1.1,
              maxWidth: "600px",
            }}
          >
            Three tools, one conversation.
          </h2>

          {/* Bento grid */}
          <div style={{ borderRadius: "16px", overflow: "hidden", border: "1px solid #e5e7eb" }}>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-px" style={{ background: "#e5e7eb" }}>

              {/* RAG — large */}
              <div className="md:col-span-3 p-8 group relative overflow-hidden bg-white">
                <div
                  className="pointer-events-none absolute -top-16 -right-16 w-48 h-48 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-700"
                  aria-hidden="true"
                  style={{ background: "radial-gradient(circle, rgba(16,185,129,0.06), transparent 70%)" }}
                />
                <div className="pointer-events-none absolute top-6 right-8" aria-hidden="true" style={{ opacity: 0.06 }}>
                  <div className="w-16 h-20 rounded-md border border-gray-400 mb-[-16px] ml-2" />
                  <div className="w-16 h-20 rounded-md border border-gray-400 mb-[-16px] ml-1" />
                  <div className="w-16 h-20 rounded-md border border-gray-400" />
                </div>
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center mb-6"
                  style={{ background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.15)" }}
                  aria-hidden="true"
                >
                  <Files size={18} weight="duotone" style={{ color: "#10b981" }} />
                </div>
                <h3 className="text-base font-semibold mb-3 tracking-tight" style={{ color: "#0a0a0a" }}>
                  Retrieval-Augmented Generation
                </h3>
                <p className="text-[0.9375rem] leading-relaxed mb-8" style={{ color: "#525252", maxWidth: "340px" }}>
                  Drop PDFs, Word docs, Notion exports, CSVs. The agent searches
                  semantically &mdash; no keyword matching, no hallucination.
                </p>
                <div className="flex items-center gap-2 flex-wrap" aria-hidden="true">
                  {["PDF", "CSV", "DOCX", "MD", "TXT"].map((ext) => (
                    <div
                      key={ext}
                      className="px-2.5 py-1 rounded-md text-[11px] font-semibold"
                      style={{ background: "#f7f7f8", border: "1px solid #e5e7eb", color: "#9ca3af" }}
                    >
                      {ext}
                    </div>
                  ))}
                  <ArrowRight size={10} style={{ color: "#d1d5db" }} aria-hidden="true" />
                  <div
                    className="px-2.5 py-1 rounded-md text-[11px] font-semibold"
                    style={{ background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.18)", color: "#10b981" }}
                  >
                    Answer
                  </div>
                </div>
              </div>

              {/* Right column */}
              <div className="md:col-span-2 flex flex-col gap-px" style={{ background: "#e5e7eb" }}>

                {/* Database */}
                <div className="flex-1 p-6 group relative overflow-hidden bg-white">
                  <div
                    className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                    aria-hidden="true"
                    style={{ background: "radial-gradient(ellipse 70% 70% at 50% 100%, rgba(16,185,129,0.03), transparent)" }}
                  />
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center mb-4"
                    style={{ background: "#f7f7f8", border: "1px solid #e5e7eb" }}
                    aria-hidden="true"
                  >
                    <Database size={16} weight="duotone" style={{ color: "#6b7280" }} />
                  </div>
                  <h3 className="text-sm font-semibold mb-2 tracking-tight" style={{ color: "#0a0a0a" }}>
                    Database Query
                  </h3>
                  <p className="text-xs leading-relaxed mb-5" style={{ color: "#6b7280" }}>
                    Ask in plain English. No SQL required.
                  </p>
                  <div
                    className="px-3 py-2 rounded-lg font-mono text-[10px] leading-relaxed"
                    style={{ background: "#f7f7f8", border: "1px solid #e5e7eb" }}
                    aria-hidden="true"
                  >
                    <span style={{ color: "#10b981" }}>SELECT</span>{" "}
                    <span style={{ color: "#6b7280" }}>revenue, churn</span>{" "}
                    <span style={{ color: "#10b981" }}>FROM</span>{" "}
                    <span style={{ color: "#6b7280" }}>metrics</span>
                    <span
                      className="inline-block w-0.5 h-3 ml-0.5 align-middle rounded-sm"
                      style={{ background: "rgba(16,185,129,0.5)", animation: "blink 1s step-end infinite" }}
                      aria-hidden="true"
                    />
                  </div>
                </div>

                {/* Web browsing */}
                <div className="flex-1 p-6 group relative overflow-hidden bg-white">
                  <div
                    className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                    aria-hidden="true"
                    style={{ background: "radial-gradient(ellipse 70% 70% at 50% 0%, rgba(16,185,129,0.03), transparent)" }}
                  />
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center mb-4"
                    style={{ background: "#f7f7f8", border: "1px solid #e5e7eb" }}
                    aria-hidden="true"
                  >
                    <Globe size={16} weight="duotone" style={{ color: "#6b7280" }} />
                  </div>
                  <h3 className="text-sm font-semibold mb-2 tracking-tight" style={{ color: "#0a0a0a" }}>
                    Live Web Browsing
                  </h3>
                  <p className="text-xs leading-relaxed mb-5" style={{ color: "#6b7280" }}>
                    Beyond training data. Real-time access.
                  </p>
                  <div
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
                    style={{ background: "#f7f7f8", border: "1px solid #e5e7eb" }}
                    aria-hidden="true"
                  >
                    <Globe size={9} style={{ color: "rgba(16,185,129,0.6)" }} className="shrink-0" />
                    <span className="text-[10px] font-mono flex-1 truncate" style={{ color: "#9ca3af" }}>
                      fetching live data&hellip;
                    </span>
                    <span
                      className="w-1.5 h-1.5 rounded-full shrink-0"
                      style={{ background: "#10b981", animation: "dotPulse 1.4s ease-in-out infinite" }}
                      aria-hidden="true"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Row 2 */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-px" style={{ background: "#e5e7eb", borderTop: "1px solid #e5e7eb" }}>
              {/* Agentic reasoning */}
              <div className="p-7 group relative overflow-hidden bg-white">
                <div
                  className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                  aria-hidden="true"
                  style={{ background: "radial-gradient(ellipse 60% 60% at 50% 0%, rgba(16,185,129,0.03), transparent)" }}
                />
                <div className="flex items-start gap-4">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                    style={{ background: "#f7f7f8", border: "1px solid #e5e7eb" }}
                    aria-hidden="true"
                  >
                    <GitBranch size={18} weight="duotone" style={{ color: "#6b7280" }} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold mb-1.5 tracking-tight" style={{ color: "#0a0a0a" }}>
                      Agentic Reasoning
                    </h3>
                    <p className="text-[0.9375rem] leading-relaxed" style={{ color: "#525252" }}>
                      Chains multiple tool calls automatically. Multi-step queries, zero manual prompting.
                    </p>
                  </div>
                </div>
                <div className="mt-6 flex items-center flex-wrap" aria-hidden="true">
                  {["Search docs", "Query DB", "Browse web", "Synthesize"].map((step, i) => (
                    <div key={step} className="flex items-center">
                      <div
                        className="px-2.5 py-1 rounded text-[10px] font-medium"
                        style={{ background: "#f7f7f8", border: "1px solid #e5e7eb", color: "#9ca3af" }}
                      >
                        {step}
                      </div>
                      {i < 3 && (
                        <div className="w-5 h-px mx-0.5" style={{ background: "#e5e7eb" }} />
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Real-time streaming */}
              <div className="p-7 group relative overflow-hidden bg-white">
                <div
                  className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                  aria-hidden="true"
                  style={{ background: "radial-gradient(ellipse 60% 60% at 50% 0%, rgba(16,185,129,0.03), transparent)" }}
                />
                <div className="flex items-start gap-4">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                    style={{ background: "#f7f7f8", border: "1px solid #e5e7eb" }}
                    aria-hidden="true"
                  >
                    <Lightning size={18} weight="duotone" style={{ color: "#6b7280" }} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold mb-1.5 tracking-tight" style={{ color: "#0a0a0a" }}>
                      Streams in real-time
                    </h3>
                    <p className="text-[0.9375rem] leading-relaxed" style={{ color: "#525252" }}>
                      See tokens arrive as they generate. Tool calls surface inline &mdash; nothing hidden.
                    </p>
                  </div>
                </div>
                <div className="mt-6 relative" aria-hidden="true">
                  <div className="space-y-2">
                    <div className="h-1.5 rounded-full" style={{ width: "85%", background: "#f0f0f1" }} />
                    <div className="h-1.5 rounded-full" style={{ width: "62%", background: "#f0f0f1" }} />
                    <div className="h-1.5 rounded-full" style={{ width: "74%", background: "#f3f4f6" }} />
                    <div
                      className="h-1.5 rounded-full"
                      style={{
                        width: "40%",
                        background: "linear-gradient(90deg, rgba(16,185,129,0.25) 0%, rgba(16,185,129,0.05) 100%)",
                        animation: "lineGrow 2s ease-out infinite",
                      }}
                    />
                  </div>
                  <span className="absolute top-0 right-0 text-[9px] font-mono" style={{ color: "#d1d5db" }}>
                    1,847 tokens
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── How it works ── */}
        <section
          className="relative px-6 md:px-10 pt-32 pb-24"
          style={{ maxWidth: "1400px", margin: "0 auto" }}
          aria-labelledby="how-it-works-heading"
        >
          <div className="flex items-center gap-3 mb-5">
            <p className="text-xs font-semibold tracking-[0.18em] uppercase shrink-0" style={{ color: "#10b981" }}>
              How it works
            </p>
            <span className="flex-1 h-px" style={{ background: "#f0f0f1" }} aria-hidden="true" />
          </div>

          <h2
            id="how-it-works-heading"
            className="mb-16"
            style={{
              fontFamily: "var(--font-geist-sans), system-ui, sans-serif",
              fontStyle: "normal",
              fontWeight: 700,
              fontSize: "clamp(1.75rem, 3.5vw, 2.5rem)",
              letterSpacing: "-0.035em",
              color: "#0a0a0a",
              lineHeight: 1.1,
              maxWidth: "560px",
            }}
          >
            Up in minutes, not hours.
          </h2>

          <div className="relative max-w-2xl">
            <div
              className="absolute left-[15px] top-0 bottom-0 w-px hidden sm:block"
              style={{ background: "linear-gradient(to bottom, rgba(16,185,129,0.3), rgba(16,185,129,0.05))" }}
              aria-hidden="true"
            />
            <div className="flex flex-col gap-16">
              {[
                {
                  n: "01",
                  title: "Drop your data",
                  body: "Documents, database connections, URLs \u2014 bring whatever you have. No formatting required.",
                },
                {
                  n: "02",
                  title: "Ask anything",
                  body: "Plain language questions. No SQL, no search syntax \u2014 just describe what you want to know.",
                },
                {
                  n: "03",
                  title: "Get cited answers",
                  body: "Every claim is traced to a source. See exactly which documents, rows, and pages were used.",
                },
              ].map(({ n, title, body }) => (
                <div key={n} className="flex items-start gap-6 sm:gap-8">
                  <div className="flex flex-col items-center shrink-0">
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-mono font-semibold relative z-10"
                      style={{
                        background: "#ffffff",
                        border: "1px solid rgba(16,185,129,0.25)",
                        color: "#10b981",
                      }}
                    >
                      {n}
                    </div>
                  </div>
                  <div className="pt-1">
                    <h3 className="text-base font-semibold mb-2 tracking-tight" style={{ color: "#0a0a0a" }}>
                      {title}
                    </h3>
                    <p className="text-[0.9375rem] leading-relaxed" style={{ color: "#525252", maxWidth: "420px" }}>
                      {body}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── CTA ── */}
        <section
          className="relative px-6 md:px-10 pt-8 pb-28"
          style={{ maxWidth: "1400px", margin: "0 auto" }}
          aria-labelledby="cta-heading"
        >
          <div className="mb-24" style={{ height: "1px", background: "#f0f0f1" }} />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 md:gap-16 items-start">
            <div>
              <p className="text-xs font-semibold tracking-[0.18em] uppercase mb-7" style={{ color: "#10b981" }}>
                Ready when you are
              </p>
              <h2
                id="cta-heading"
                className="mb-7"
                style={{
                  fontFamily: "var(--font-geist-sans), system-ui, sans-serif",
                  fontStyle: "normal",
                  fontWeight: 700,
                  fontSize: "clamp(1.875rem, 4.5vw, 3rem)",
                  letterSpacing: "-0.04em",
                  color: "#0a0a0a",
                  lineHeight: 1.08,
                  maxWidth: "480px",
                }}
              >
                Intelligence across
                <br />
                all your data.
              </h2>
              <Link
                href="/chat"
                className="lp-btn-primary inline-flex items-center gap-2 px-8 py-3.5 text-sm font-semibold rounded-full text-white"
                style={{
                  boxShadow: "0 1px 3px rgba(0,0,0,0.1), 0 6px 20px rgba(0,0,0,0.12)",
                }}
              >
                Get started free
                <ArrowUpRight size={14} weight="bold" aria-hidden="true" />
              </Link>
              <p className="mt-5 text-xs" style={{ color: "#9ca3af" }}>No credit card required</p>
            </div>

            <div className="flex flex-col gap-4 md:pt-16">
              {[
                { label: "Sign in with GitHub or Google", detail: "No passwords, no API keys" },
                { label: "Your data stays yours", detail: "Self-hostable, open-source" },
                { label: "Free to use", detail: "No usage limits, no paywall" },
              ].map(({ label, detail }) => (
                <div key={label} className="flex items-start gap-3">
                  <CheckCircle size={18} weight="fill" className="shrink-0 mt-0.5" style={{ color: "#10b981" }} />
                  <div>
                    <p className="text-sm font-medium" style={{ color: "#0a0a0a" }}>{label}</p>
                    <p className="text-xs mt-0.5" style={{ color: "#6b7280" }}>{detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

      </main>

      {/* ── Footer ── */}
      <footer
        className="px-6 md:px-10 py-8"
        style={{ borderTop: "1px solid #f0f0f1", maxWidth: "1400px", margin: "0 auto" }}
        role="contentinfo"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: "#10b981" }} aria-hidden="true" />
            <span className="text-xs font-semibold" style={{ color: "#9ca3af" }}>AgenticRAG</span>
          </div>
          <p className="text-xs" style={{ color: "#d1d5db" }}>
            Built with AI &mdash; for humans who want answers.
          </p>
        </div>
      </footer>

    </div>
  );
}
