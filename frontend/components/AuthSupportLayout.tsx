"use client";

import Link from "next/link";

interface AuthSupportLayoutProps {
  eyebrow: string;
  title: string;
  description: string;
  sideTitle: string;
  sideDescription: string;
  sidePoints: string[];
  children: React.ReactNode;
  backHref?: string;
  backLabel?: string;
}

export default function AuthSupportLayout({
  eyebrow,
  title,
  description,
  sideTitle,
  sideDescription,
  sidePoints,
  children,
  backHref = "/auth/signin",
  backLabel = "Back to sign in",
}: AuthSupportLayoutProps) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-black text-zinc-100">
      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-6xl items-center px-6 py-10">
        <div className="hidden flex-1 pr-12 lg:block">
          <p className="mb-3 text-xs uppercase tracking-[0.24em] text-violet-300/80">
            RunaxAI
          </p>
          <h1 className="max-w-xl text-4xl font-semibold leading-tight tracking-tight text-zinc-100">
            {sideTitle}
          </h1>
          <p className="mt-5 max-w-lg text-base leading-relaxed text-zinc-400">
            {sideDescription}
          </p>
          <div className="mt-8 space-y-3">
            {sidePoints.map((point) => (
              <div key={point} className="flex items-center gap-3 text-sm text-zinc-300">
                <span className="h-2 w-2 rounded-full bg-violet-300/80" />
                <span>{point}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#151515]/95 p-7 shadow-[0_24px_80px_rgba(0,0,0,0.55)] backdrop-blur">
          <Link
            href={backHref}
            className="inline-flex text-xs uppercase tracking-[0.22em] text-zinc-500 transition-colors hover:text-zinc-300"
          >
            {backLabel}
          </Link>
          <h2 className="mt-4 text-2xl font-semibold tracking-tight text-zinc-100">{title}</h2>
          <p className="mt-1 text-sm text-zinc-400">{description}</p>
          <p className="mt-6 text-xs uppercase tracking-[0.24em] text-violet-300/80">
            {eyebrow}
          </p>
          <div className="mt-4">{children}</div>
        </div>
      </div>
    </div>
  );
}
