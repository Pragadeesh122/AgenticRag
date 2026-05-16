import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: {
    default: "RunaxAI Blog",
    template: "%s — RunaxAI Blog",
  },
  description:
    "Design notes, engineering decisions, and product updates from RunaxAI.",
};

export default function BlogLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0c0c0d] text-zinc-200">
      <header className="border-b border-white/5">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-5">
          <Link
            href="/blog"
            className="flex items-baseline gap-2 text-[15px] font-medium tracking-tight text-zinc-100 transition-colors hover:text-white"
          >
            <span className="text-emerald-400">/</span>
            RunaxAI
            <span className="text-zinc-500">blog</span>
          </Link>
          <nav className="flex items-center gap-6 text-[13px] text-zinc-400">
            <Link
              href="/blog"
              className="transition-colors hover:text-zinc-100"
            >
              Posts
            </Link>
            <a
              href="https://runaxai.com"
              className="transition-colors hover:text-zinc-100"
            >
              runaxai.com
            </a>
          </nav>
        </div>
      </header>
      <main>{children}</main>
      <footer className="mt-24 border-t border-white/5">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-8 text-[12px] text-zinc-500">
          <span>© {new Date().getFullYear()} RunaxAI</span>
          <a
            href="https://runaxai.com"
            className="transition-colors hover:text-zinc-300"
          >
            Try the app →
          </a>
        </div>
      </footer>
    </div>
  );
}
