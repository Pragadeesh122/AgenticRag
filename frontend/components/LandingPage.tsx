import Link from "next/link";
import { MagnifyingGlass } from "@phosphor-icons/react/dist/ssr/MagnifyingGlass";
import { Database } from "@phosphor-icons/react/dist/ssr/Database";
import { Globe } from "@phosphor-icons/react/dist/ssr/Globe";
import { ArrowRight } from "@phosphor-icons/react/dist/ssr/ArrowRight";
import { Files } from "@phosphor-icons/react/dist/ssr/Files";
import { GitBranch } from "@phosphor-icons/react/dist/ssr/GitBranch";
import { Lightning } from "@phosphor-icons/react/dist/ssr/Lightning";
import { CheckCircle } from "@phosphor-icons/react/dist/ssr/CheckCircle";
import { ArrowUpRight } from "@phosphor-icons/react/dist/ssr/ArrowUpRight";

export default function LandingPage() {
  return (
    <div className="min-h-screen overflow-x-hidden" style={{ background: "#0a0a0a", color: "#e8e8e8" }}>

      {/* ── Navbar ── */}
      <header
        className="sticky top-0 z-50 w-full"
        style={{
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          background: "rgba(10,10,10,0.9)",
          backdropFilter: "blur(16px)",
          WebkitBackdropFilter: "blur(16px)",
        }}
        role="banner"
      >
        <div className="max-w-6xl mx-auto px-8 h-[56px] flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5" aria-label="AgenticRAG home">
            <div
              className="w-6 h-6 rounded-[6px] flex items-center justify-center shrink-0"
              style={{ background: "rgba(16,185,129,0.15)", border: "1px solid rgba(16,185,129,0.25)" }}
              aria-hidden="true"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="4" fill="#10b981" fillOpacity="0.9" />
                <circle cx="12" cy="12" r="8" stroke="#10b981" strokeWidth="1.5" strokeOpacity="0.35" />
                <line x1="12" y1="2" x2="12" y2="6" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" strokeOpacity="0.5" />
                <line x1="12" y1="18" x2="12" y2="22" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" strokeOpacity="0.5" />
                <line x1="2" y1="12" x2="6" y2="12" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" strokeOpacity="0.5" />
                <line x1="18" y1="12" x2="22" y2="12" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" strokeOpacity="0.5" />
              </svg>
            </div>
            <span className="text-sm font-semibold tracking-tight" style={{ color: "rgba(255,255,255,0.9)" }}>
              AgenticRAG
            </span>
          </Link>

          <nav aria-label="Main navigation" className="flex items-center gap-1">
            <Link
              href="/auth/signin"
              className="lp-nav-signin px-4 py-1.5 text-sm rounded-full"
            >
              Sign in
            </Link>
            <Link
              href="/auth/signin"
              className="lp-btn-primary inline-flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium rounded-full"
              style={{ color: "#fff" }}
            >
              Get started
            </Link>
          </nav>
        </div>
      </header>

      <main>

        {/* ── Hero ── */}
        <section
          className="relative px-8 pt-28 pb-0"
          style={{ maxWidth: "1152px", margin: "0 auto" }}
          aria-labelledby="hero-heading"
        >

          {/* Background grid — very subtle */}
          <div
            className="pointer-events-none absolute inset-0"
            aria-hidden="true"
            style={{
              backgroundImage: `
                linear-gradient(rgba(255,255,255,0.028) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.028) 1px, transparent 1px)
              `,
              backgroundSize: "80px 80px",
              maskImage: "radial-gradient(ellipse 80% 60% at 30% 40%, black 20%, transparent 80%)",
              WebkitMaskImage: "radial-gradient(ellipse 80% 60% at 30% 40%, black 20%, transparent 80%)",
            }}
          />

          {/* Emerald glow — top-left anchored */}
          <div
            className="pointer-events-none absolute"
            aria-hidden="true"
            style={{
              top: "-80px",
              left: "-120px",
              width: "600px",
              height: "500px",
              background: "radial-gradient(ellipse at center, rgba(16,185,129,0.07) 0%, transparent 70%)",
              filter: "blur(40px)",
            }}
          />

          {/* Eyebrow */}
          <div
            className="inline-flex items-center gap-2 mb-8"
            style={{ animationDelay: "0ms" }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: "#10b981" }}
              aria-hidden="true"
            />
            <span className="text-xs font-medium tracking-[0.1em] uppercase" style={{ color: "rgba(16,185,129,0.8)" }}>
              Open-source · Agentic RAG
            </span>
          </div>

          {/* Hero headline — left-aligned, Linear style */}
          <h1
            id="hero-heading"
            className="relative"
            style={{
              maxWidth: "820px",
              marginBottom: "28px",
            }}
          >
            {/* Line 1 — large serif italic */}
            <span
              className="block"
              style={{
                fontFamily: "var(--font-serif), Georgia, serif",
                fontStyle: "italic",
                fontWeight: 400,
                fontSize: "clamp(3rem, 7vw, 5.5rem)",
                lineHeight: 1.0,
                letterSpacing: "-0.03em",
                color: "rgba(255,255,255,0.92)",
              }}
            >
              Ask anything.
            </span>
            {/* Line 2 — serif italic + emerald gradient */}
            <span
              className="block"
              style={{
                fontFamily: "var(--font-serif), Georgia, serif",
                fontStyle: "italic",
                fontWeight: 400,
                fontSize: "clamp(3rem, 7vw, 5.5rem)",
                lineHeight: 1.05,
                letterSpacing: "-0.03em",
                background: "linear-gradient(120deg, #10b981 0%, #34d399 50%, #6ee7b7 100%)",
                backgroundClip: "text",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                marginTop: "4px",
              }}
            >
              Get grounded answers.
            </span>
          </h1>

          {/* Subtitle */}
          <p
            className="text-base leading-relaxed mb-10"
            style={{
              maxWidth: "440px",
              color: "rgba(255,255,255,0.38)",
              fontSize: "1.0625rem",
            }}
          >
            Connect your documents, databases, and the web. AgenticRAG reasons
            across all of it and shows its work.
          </p>

          {/* CTA row */}
          <div className="flex flex-col sm:flex-row items-start gap-3 mb-24">
            <Link
              href="/auth/signin"
              className="lp-btn-primary inline-flex items-center gap-2 px-6 py-3 text-sm font-semibold rounded-full"
              style={{
                color: "#fff",
                boxShadow: "0 0 0 1px rgba(16,185,129,0.4), 0 8px 24px rgba(16,185,129,0.2)",
              }}
            >
              Start for free
              <ArrowRight size={14} weight="bold" aria-hidden="true" />
            </Link>
            <Link
              href="/auth/signin"
              className="lp-btn-ghost inline-flex items-center gap-2 px-6 py-3 text-sm font-medium rounded-full"
            >
              Sign in
            </Link>
          </div>
        </section>

        {/* ── Hero Demo — full bleed card ── */}
        <section
          className="relative px-8 pb-16"
          style={{ maxWidth: "1152px", margin: "0 auto" }}
          aria-label="Product demo"
        >
          {/* Ambient glow behind card */}
          <div
            className="pointer-events-none absolute inset-x-8 top-0"
            aria-hidden="true"
            style={{
              height: "300px",
              background: "radial-gradient(ellipse 60% 100% at 50% 0%, rgba(16,185,129,0.05), transparent)",
            }}
          />

          {/* App window chrome */}
          <div
            className="relative overflow-hidden"
            style={{
              borderRadius: "16px",
              border: "1px solid rgba(255,255,255,0.08)",
              background: "rgba(255,255,255,0.02)",
              boxShadow: "0 32px 100px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.03) inset",
            }}
          >
            {/* Window titlebar */}
            <div
              className="flex items-center gap-3 px-5 py-3"
              style={{
                borderBottom: "1px solid rgba(255,255,255,0.05)",
                background: "rgba(255,255,255,0.015)",
              }}
              aria-hidden="true"
            >
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full" style={{ background: "rgba(255,255,255,0.08)" }} />
                <div className="w-3 h-3 rounded-full" style={{ background: "rgba(255,255,255,0.08)" }} />
                <div className="w-3 h-3 rounded-full" style={{ background: "rgba(255,255,255,0.08)" }} />
              </div>
              {/* Fake URL bar */}
              <div
                className="flex-1 mx-4 h-6 rounded-md flex items-center px-3 gap-2"
                style={{ background: "rgba(255,255,255,0.04)", maxWidth: "340px", margin: "0 auto" }}
              >
                <div className="w-2 h-2 rounded-full" style={{ background: "rgba(16,185,129,0.6)" }} />
                <span className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.2)" }}>
                  agenticrag.app / chat
                </span>
              </div>
              <div className="ml-auto flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: "#10b981" }} />
                <span className="text-[10px] font-medium" style={{ color: "rgba(16,185,129,0.7)" }}>Live</span>
              </div>
            </div>

            {/* App body — 2 columns: sidebar + chat */}
            <div className="flex" style={{ minHeight: "420px" }}>

              {/* Sidebar */}
              <div
                className="w-52 shrink-0 p-4 flex flex-col gap-1"
                style={{
                  borderRight: "1px solid rgba(255,255,255,0.05)",
                  background: "rgba(0,0,0,0.15)",
                }}
                aria-hidden="true"
              >
                {/* Logo row */}
                <div className="flex items-center gap-2 px-2 py-2 mb-2">
                  <div className="w-5 h-5 rounded-md" style={{ background: "rgba(16,185,129,0.2)" }} />
                  <span className="text-xs font-semibold" style={{ color: "rgba(255,255,255,0.5)" }}>AgenticRAG</span>
                </div>

                {/* New chat button */}
                <div
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg mb-3"
                  style={{ background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.2)" }}
                >
                  <span className="text-xs font-medium" style={{ color: "rgba(16,185,129,0.85)" }}>+ New chat</span>
                </div>

                {/* Session list */}
                {[
                  { label: "Q3 churn analysis", active: true },
                  { label: "Revenue by segment" },
                  { label: "Competitor pricing" },
                  { label: "User onboarding data" },
                ].map(({ label, active }) => (
                  <div
                    key={label}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-md"
                    style={{
                      background: active ? "rgba(255,255,255,0.06)" : "transparent",
                      borderLeft: active ? "2px solid rgba(16,185,129,0.6)" : "2px solid transparent",
                    }}
                  >
                    <span
                      className="text-xs truncate"
                      style={{ color: active ? "rgba(255,255,255,0.75)" : "rgba(255,255,255,0.28)" }}
                    >
                      {label}
                    </span>
                  </div>
                ))}
              </div>

              {/* Chat area */}
              <div className="flex-1 flex flex-col" role="presentation" aria-label="Example conversation">
                {/* Messages */}
                <div className="flex-1 px-8 py-7 space-y-5 overflow-hidden">

                  {/* User message */}
                  <div className="flex justify-end">
                    <div
                      className="max-w-sm px-4 py-3 rounded-2xl text-sm"
                      style={{
                        background: "rgba(16,185,129,0.08)",
                        border: "1px solid rgba(16,185,129,0.16)",
                        color: "rgba(255,255,255,0.82)",
                        lineHeight: "1.5",
                      }}
                    >
                      What does our Q3 report say about churn, and how does it compare to industry benchmarks?
                    </div>
                  </div>

                  {/* Tool call — RAG search */}
                  <div
                    className="flex items-start gap-3 px-4 py-3 rounded-xl"
                    style={{
                      background: "rgba(255,255,255,0.03)",
                      border: "1px solid rgba(255,255,255,0.07)",
                      maxWidth: "560px",
                    }}
                  >
                    <div
                      className="mt-0.5 w-6 h-6 rounded-lg flex items-center justify-center shrink-0"
                      style={{ background: "rgba(16,185,129,0.12)", border: "1px solid rgba(16,185,129,0.18)" }}
                      aria-hidden="true"
                    >
                      <MagnifyingGlass size={12} weight="bold" style={{ color: "#10b981" }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold font-mono" style={{ color: "#10b981" }}>rag_search</p>
                      <p className="text-xs mt-0.5 leading-relaxed" style={{ color: "rgba(255,255,255,0.3)" }}>
                        Searching &ldquo;Q3 churn analysis&rdquo; across 847 documents&hellip;
                      </p>
                    </div>
                    <div className="ml-auto shrink-0 flex items-center gap-1.5">
                      <CheckCircle size={12} weight="fill" style={{ color: "rgba(16,185,129,0.7)" }} aria-hidden="true" />
                      <span className="text-[10px] font-medium" style={{ color: "rgba(16,185,129,0.6)" }}>Done</span>
                    </div>
                  </div>

                  {/* Tool call — Web search */}
                  <div
                    className="flex items-start gap-3 px-4 py-3 rounded-xl"
                    style={{
                      background: "rgba(255,255,255,0.03)",
                      border: "1px solid rgba(255,255,255,0.07)",
                      maxWidth: "560px",
                    }}
                  >
                    <div
                      className="mt-0.5 w-6 h-6 rounded-lg flex items-center justify-center shrink-0"
                      style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)" }}
                      aria-hidden="true"
                    >
                      <Globe size={12} weight="bold" style={{ color: "rgba(255,255,255,0.45)" }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold font-mono" style={{ color: "rgba(255,255,255,0.55)" }}>web_search</p>
                      <p className="text-xs mt-0.5 leading-relaxed" style={{ color: "rgba(255,255,255,0.3)" }}>
                        Fetching SaaS churn benchmarks 2024&hellip;
                      </p>
                    </div>
                    <div className="ml-auto shrink-0 flex items-center gap-1.5">
                      <CheckCircle size={12} weight="fill" style={{ color: "rgba(16,185,129,0.7)" }} aria-hidden="true" />
                      <span className="text-[10px] font-medium" style={{ color: "rgba(16,185,129,0.6)" }}>Done</span>
                    </div>
                  </div>

                  {/* Assistant response */}
                  <div className="space-y-2" style={{ maxWidth: "560px" }}>
                    <p className="text-[10px] font-semibold tracking-[0.12em] uppercase" style={{ color: "rgba(255,255,255,0.2)" }}>
                      AgenticRAG
                    </p>
                    <p className="text-sm leading-relaxed" style={{ color: "rgba(255,255,255,0.62)" }}>
                      Your Q3 report shows{" "}
                      <span className="font-semibold" style={{ color: "rgba(255,255,255,0.88)" }}>4.2% monthly churn</span>
                      {" "}— 1.8 points above the industry median of 2.4% for B2B SaaS. The report
                      attributes this to onboarding drop-off in weeks 2–3&hellip;
                    </p>
                    <span
                      className="inline-block w-0.5 h-3.5 rounded-sm align-middle"
                      style={{
                        background: "#10b981",
                        animation: "blink 1s step-end infinite",
                        verticalAlign: "middle",
                        opacity: 0.7,
                      }}
                      aria-hidden="true"
                    />
                  </div>
                </div>

                {/* Input bar */}
                <div
                  className="px-8 py-4"
                  style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}
                  aria-hidden="true"
                >
                  <div
                    className="flex items-center gap-3 px-4 py-2.5 rounded-xl"
                    style={{
                      background: "rgba(255,255,255,0.03)",
                      border: "1px solid rgba(255,255,255,0.08)",
                    }}
                  >
                    <span className="flex-1 text-sm" style={{ color: "rgba(255,255,255,0.18)" }}>
                      Ask a follow-up question&hellip;
                    </span>
                    <div
                      className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
                      style={{ background: "rgba(16,185,129,0.15)", border: "1px solid rgba(16,185,129,0.25)" }}
                    >
                      <ArrowRight size={12} weight="bold" style={{ color: "#10b981" }} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Fade bottom of card */}
          <div
            className="pointer-events-none absolute bottom-28 left-8 right-8 h-20 rounded-b-2xl"
            aria-hidden="true"
            style={{ background: "linear-gradient(to bottom, transparent, rgba(10,10,10,0.5))" }}
          />
        </section>

        {/* ── Thin divider ── */}
        <div className="max-w-6xl mx-auto px-8">
          <div style={{ height: "1px", background: "rgba(255,255,255,0.05)" }} />
        </div>

        {/* ── Capabilities ── */}
        <section
          className="relative px-8 py-28"
          style={{ maxWidth: "1152px", margin: "0 auto" }}
          aria-labelledby="capabilities-heading"
        >

          {/* Section label */}
          <p
            className="text-xs font-semibold tracking-[0.18em] uppercase mb-5"
            style={{ color: "rgba(16,185,129,0.55)" }}
          >
            Capabilities
          </p>

          <h2
            id="capabilities-heading"
            className="mb-16"
            style={{
              fontFamily: "var(--font-serif), Georgia, serif",
              fontStyle: "italic",
              fontWeight: 400,
              fontSize: "clamp(1.875rem, 4vw, 2.75rem)",
              letterSpacing: "-0.025em",
              color: "rgba(255,255,255,0.88)",
              lineHeight: 1.1,
              maxWidth: "600px",
            }}
          >
            Three tools, one conversation.
          </h2>

          {/* Bento grid — single unified container */}
          <div style={{ borderRadius: "16px", overflow: "hidden", border: "1px solid rgba(255,255,255,0.07)" }}>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-px" style={{ background: "rgba(255,255,255,0.06)" }}>

            {/* RAG — large */}
            <div
              className="md:col-span-3 p-8 group relative overflow-hidden"
              style={{ background: "#0a0a0a" }}
            >
              <div
                className="pointer-events-none absolute -top-16 -right-16 w-48 h-48 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-700"
                aria-hidden="true"
                style={{ background: "radial-gradient(circle, rgba(16,185,129,0.12), transparent 70%)", filter: "blur(32px)" }}
              />
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center mb-6"
                style={{ background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.18)" }}
                aria-hidden="true"
              >
                <Files size={18} weight="duotone" style={{ color: "#10b981" }} />
              </div>
              <h3
                className="text-base font-semibold mb-3 tracking-tight"
                style={{ color: "rgba(255,255,255,0.88)" }}
              >
                Retrieval-Augmented Generation
              </h3>
              <p className="text-sm leading-relaxed mb-8" style={{ color: "rgba(255,255,255,0.36)", maxWidth: "340px" }}>
                Drop PDFs, Word docs, Notion exports, CSVs. The agent searches
                semantically — no keyword matching, no hallucination.
              </p>
              {/* Format chips */}
              <div className="flex items-center gap-2 flex-wrap" aria-hidden="true">
                {["PDF", "CSV", "DOCX", "MD", "TXT"].map((ext) => (
                  <div
                    key={ext}
                    className="px-2.5 py-1 rounded-md text-[10px] font-semibold"
                    style={{
                      background: "rgba(255,255,255,0.04)",
                      border: "1px solid rgba(255,255,255,0.08)",
                      color: "rgba(255,255,255,0.32)",
                    }}
                  >
                    {ext}
                  </div>
                ))}
                <ArrowRight size={10} style={{ color: "rgba(255,255,255,0.15)" }} aria-hidden="true" />
                <div
                  className="px-2.5 py-1 rounded-md text-[10px] font-semibold"
                  style={{
                    background: "rgba(16,185,129,0.1)",
                    border: "1px solid rgba(16,185,129,0.22)",
                    color: "#10b981",
                  }}
                >
                  Answer
                </div>
              </div>
            </div>

            {/* Right column */}
            <div className="md:col-span-2 flex flex-col gap-px" style={{ background: "rgba(255,255,255,0.06)" }}>

              {/* Database */}
              <div
                className="flex-1 p-6 group relative overflow-hidden"
                style={{ background: "#0a0a0a" }}
              >
                <div
                  className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                  aria-hidden="true"
                  style={{ background: "radial-gradient(ellipse 70% 70% at 50% 100%, rgba(16,185,129,0.05), transparent)" }}
                />
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center mb-4"
                  style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.09)" }}
                  aria-hidden="true"
                >
                  <Database size={16} weight="duotone" style={{ color: "rgba(255,255,255,0.5)" }} />
                </div>
                <h3
                  className="text-sm font-semibold mb-2 tracking-tight"
                  style={{ color: "rgba(255,255,255,0.88)" }}
                >
                  Database Query
                </h3>
                <p className="text-xs leading-relaxed mb-5" style={{ color: "rgba(255,255,255,0.35)" }}>
                  Ask in plain English. No SQL required.
                </p>
                <div
                  className="px-3 py-2 rounded-lg font-mono text-[10px] leading-relaxed"
                  style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
                  aria-hidden="true"
                >
                  <span style={{ color: "rgba(16,185,129,0.65)" }}>SELECT</span>{" "}
                  <span style={{ color: "rgba(255,255,255,0.32)" }}>revenue, churn</span>{" "}
                  <span style={{ color: "rgba(16,185,129,0.65)" }}>FROM</span>{" "}
                  <span style={{ color: "rgba(255,255,255,0.32)" }}>metrics&hellip;</span>
                </div>
              </div>

              {/* Web browsing */}
              <div
                className="flex-1 p-6 group relative overflow-hidden"
                style={{ background: "#0a0a0a" }}
              >
                <div
                  className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                  aria-hidden="true"
                  style={{ background: "radial-gradient(ellipse 70% 70% at 50% 0%, rgba(16,185,129,0.05), transparent)" }}
                />
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center mb-4"
                  style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.09)" }}
                  aria-hidden="true"
                >
                  <Globe size={16} weight="duotone" style={{ color: "rgba(255,255,255,0.5)" }} />
                </div>
                <h3
                  className="text-sm font-semibold mb-2 tracking-tight"
                  style={{ color: "rgba(255,255,255,0.88)" }}
                >
                  Live Web Browsing
                </h3>
                <p className="text-xs leading-relaxed mb-5" style={{ color: "rgba(255,255,255,0.35)" }}>
                  Beyond training data. Real-time access.
                </p>
                <div
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
                  style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
                  aria-hidden="true"
                >
                  <Globe size={9} style={{ color: "rgba(16,185,129,0.45)" }} className="shrink-0" />
                  <span className="text-[10px] font-mono flex-1 truncate" style={{ color: "rgba(255,255,255,0.22)" }}>
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

          {/* Row 2 — two cards */}
          <div
            className="grid grid-cols-1 sm:grid-cols-2 gap-px"
            style={{ background: "rgba(255,255,255,0.06)", borderTop: "1px solid rgba(255,255,255,0.06)" }}
          >
            {/* Agentic reasoning */}
            <div
              className="p-7 group relative overflow-hidden"
              style={{ background: "#0a0a0a" }}
            >
              <div
                className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                aria-hidden="true"
                style={{ background: "radial-gradient(ellipse 60% 60% at 50% 0%, rgba(16,185,129,0.04), transparent)" }}
              />
              <div className="flex items-start gap-4">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}
                  aria-hidden="true"
                >
                  <GitBranch size={18} weight="duotone" style={{ color: "rgba(255,255,255,0.45)" }} />
                </div>
                <div>
                  <h3
                    className="text-sm font-semibold mb-1.5 tracking-tight"
                    style={{ color: "rgba(255,255,255,0.88)" }}
                  >
                    Agentic Reasoning
                  </h3>
                  <p className="text-sm leading-relaxed" style={{ color: "rgba(255,255,255,0.35)" }}>
                    Chains multiple tool calls automatically. Multi-step queries, zero manual prompting.
                  </p>
                </div>
              </div>
              <div className="mt-6 flex items-center gap-1.5 flex-wrap" aria-hidden="true">
                {["Search docs", "Query DB", "Browse web", "Synthesize"].map((step, i) => (
                  <div key={step} className="flex items-center gap-1.5">
                    <div
                      className="px-2 py-1 rounded text-[9px] font-medium"
                      style={{
                        background: "rgba(255,255,255,0.03)",
                        border: "1px solid rgba(255,255,255,0.07)",
                        color: "rgba(255,255,255,0.28)",
                      }}
                    >
                      {step}
                    </div>
                    {i < 3 && (
                      <ArrowRight size={8} style={{ color: "rgba(255,255,255,0.12)" }} className="shrink-0" />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Real-time streaming */}
            <div
              className="p-7 group relative overflow-hidden"
              style={{ background: "#0a0a0a" }}
            >
              <div
                className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                aria-hidden="true"
                style={{ background: "radial-gradient(ellipse 60% 60% at 50% 0%, rgba(16,185,129,0.04), transparent)" }}
              />
              <div className="flex items-start gap-4">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}
                  aria-hidden="true"
                >
                  <Lightning size={18} weight="duotone" style={{ color: "rgba(255,255,255,0.45)" }} />
                </div>
                <div>
                  <h3
                    className="text-sm font-semibold mb-1.5 tracking-tight"
                    style={{ color: "rgba(255,255,255,0.88)" }}
                  >
                    Streams in real-time
                  </h3>
                  <p className="text-sm leading-relaxed" style={{ color: "rgba(255,255,255,0.35)" }}>
                    See tokens arrive as they generate. Tool calls surface inline — nothing hidden.
                  </p>
                </div>
              </div>
              {/* Stream lines */}
              <div className="mt-6 space-y-2" aria-hidden="true">
                {[
                  { w: "85%", delay: "0ms" },
                  { w: "62%", delay: "150ms" },
                  { w: "74%", delay: "300ms" },
                ].map(({ w, delay }, i) => (
                  <div
                    key={i}
                    className="h-1.5 rounded-full"
                    style={{
                      width: w,
                      background: "rgba(255,255,255,0.06)",
                    }}
                  />
                ))}
                <div
                  className="h-1.5 rounded-full"
                  style={{
                    width: "40%",
                    background: "linear-gradient(90deg, rgba(16,185,129,0.3) 0%, rgba(16,185,129,0.05) 100%)",
                    animation: "lineGrow 2s ease-out infinite",
                  }}
                />
              </div>
            </div>
          </div>
          </div>{/* end unified bento wrapper */}
        </section>

        {/* ── Thin divider ── */}
        <div className="max-w-6xl mx-auto px-8">
          <div style={{ height: "1px", background: "rgba(255,255,255,0.05)" }} />
        </div>

        {/* ── How it works ── */}
        <section
          className="relative px-8 py-28"
          style={{ maxWidth: "1152px", margin: "0 auto" }}
          aria-labelledby="how-it-works-heading"
        >
          <p
            className="text-xs font-semibold tracking-[0.18em] uppercase mb-5"
            style={{ color: "rgba(16,185,129,0.55)" }}
          >
            How it works
          </p>
          <h2
            id="how-it-works-heading"
            className="mb-16"
            style={{
              fontFamily: "var(--font-serif), Georgia, serif",
              fontStyle: "italic",
              fontWeight: 400,
              fontSize: "clamp(1.875rem, 4vw, 2.75rem)",
              letterSpacing: "-0.025em",
              color: "rgba(255,255,255,0.88)",
              lineHeight: 1.1,
              maxWidth: "560px",
            }}
          >
            Up in minutes, not hours.
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-12">
            {[
              {
                n: "01",
                title: "Drop your data",
                body: "Documents, database connections, URLs — bring whatever you have. No formatting required.",
              },
              {
                n: "02",
                title: "Ask anything",
                body: "Plain language questions. No SQL, no search syntax — just describe what you want to know.",
              },
              {
                n: "03",
                title: "Get grounded answers",
                body: "Every answer is sourced. See exactly which documents, rows, and pages were used.",
              },
            ].map(({ n, title, body }) => (
              <div key={n} className="group">
                <div
                  className="text-[11px] font-mono font-semibold mb-5 tracking-widest"
                  style={{ color: "rgba(16,185,129,0.4)" }}
                >
                  {n}
                </div>
                {/* Step connector line */}
                <div
                  className="h-px mb-6 transition-all duration-500 group-hover:opacity-100"
                  style={{
                    width: "32px",
                    background: "rgba(16,185,129,0.4)",
                    opacity: 0.3,
                  }}
                />
                <h3
                  className="text-base font-semibold mb-3 tracking-tight"
                  style={{ color: "rgba(255,255,255,0.88)" }}
                >
                  {title}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: "rgba(255,255,255,0.36)" }}>
                  {body}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Thin divider ── */}
        <div className="max-w-6xl mx-auto px-8">
          <div style={{ height: "1px", background: "rgba(255,255,255,0.05)" }} />
        </div>

        {/* ── CTA ── */}
        <section
          className="relative px-8 py-28 text-center"
          style={{ maxWidth: "1152px", margin: "0 auto" }}
          aria-labelledby="cta-heading"
        >
          {/* Glow */}
          <div
            className="pointer-events-none absolute inset-0"
            aria-hidden="true"
            style={{
              background: "radial-gradient(ellipse 60% 80% at 50% 50%, rgba(16,185,129,0.05), transparent)",
            }}
          />

          <p
            className="text-xs font-semibold tracking-[0.18em] uppercase mb-7"
            style={{ color: "rgba(16,185,129,0.55)" }}
          >
            Ready when you are
          </p>

          <h2
            id="cta-heading"
            className="mx-auto mb-7"
            style={{
              fontFamily: "var(--font-serif), Georgia, serif",
              fontStyle: "italic",
              fontWeight: 400,
              fontSize: "clamp(2rem, 5vw, 3.5rem)",
              letterSpacing: "-0.03em",
              color: "rgba(255,255,255,0.9)",
              lineHeight: 1.05,
              maxWidth: "680px",
            }}
          >
            Intelligence across all your data.
          </h2>

          <p
            className="mx-auto mb-10 text-base leading-relaxed"
            style={{ maxWidth: "400px", color: "rgba(255,255,255,0.35)" }}
          >
            Sign in with Google or GitHub. No setup, no config files, no API keys.
          </p>

          <Link
            href="/auth/signin"
            className="lp-btn-primary inline-flex items-center gap-2 px-8 py-3.5 text-sm font-semibold rounded-full"
            style={{
              color: "#fff",
              boxShadow: "0 0 0 1px rgba(16,185,129,0.4), 0 12px 32px rgba(16,185,129,0.22)",
            }}
          >
            Get started free
            <ArrowUpRight size={14} weight="bold" aria-hidden="true" />
          </Link>

          <p
            className="mt-5 text-xs"
            style={{ color: "rgba(255,255,255,0.18)" }}
          >
            No credit card required &nbsp;&middot;&nbsp; GitHub &amp; Google auth &nbsp;&middot;&nbsp; Free to use
          </p>
        </section>

      </main>

      {/* ── Footer ── */}
      <footer
        className="px-8 py-8"
        style={{
          borderTop: "1px solid rgba(255,255,255,0.05)",
          maxWidth: "1152px",
          margin: "0 auto",
        }}
        role="contentinfo"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className="w-5 h-5 rounded-md flex items-center justify-center"
              style={{ background: "rgba(16,185,129,0.12)", border: "1px solid rgba(16,185,129,0.18)" }}
              aria-hidden="true"
            >
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="4" fill="#10b981" fillOpacity="0.85" />
                <circle cx="12" cy="12" r="8" stroke="#10b981" strokeWidth="1.5" strokeOpacity="0.3" />
              </svg>
            </div>
            <span className="text-xs font-semibold" style={{ color: "rgba(255,255,255,0.35)" }}>AgenticRAG</span>
          </div>
          <p className="text-xs" style={{ color: "rgba(255,255,255,0.18)" }}>
            Built with AI — for humans who want answers.
          </p>
        </div>
      </footer>

    </div>
  );
}
