"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { requestPasswordReset } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await requestPasswordReset(email.trim());
      setSubmitted(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to request password reset";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#131417] text-zinc-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(124,58,237,0.18),transparent_30%),radial-gradient(circle_at_80%_10%,rgba(34,197,94,0.14),transparent_28%),radial-gradient(circle_at_40%_90%,rgba(59,130,246,0.12),transparent_32%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-[0.08] [background-image:linear-gradient(to_right,#ffffff_1px,transparent_1px),linear-gradient(to_bottom,#ffffff_1px,transparent_1px)] [background-size:42px_42px]" />

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-lg items-center px-6 py-10">
        <div className="w-full rounded-2xl border border-white/10 bg-[#1b1d21]/95 p-7 shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-100">
            Reset your password
          </h1>
          <p className="mt-2 text-sm text-zinc-400">
            Enter your account email. If the account exists, the backend will issue a reset token.
          </p>

          {submitted ? (
            <div className="mt-5 space-y-3">
              <p className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
                Reset instructions were requested. In local development, the token is logged by the backend.
              </p>
              <Link href="/auth/signin" className="text-sm text-violet-300 hover:text-violet-200">
                Back to sign in
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="mt-5 space-y-4">
              <div>
                <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-zinc-300">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  autoComplete="email"
                  required
                  className="w-full rounded-xl border border-white/10 bg-black/25 px-3 py-2.5 text-sm text-zinc-100 outline-none transition-colors placeholder:text-zinc-500 focus:border-violet-400/60"
                  placeholder="you@example.com"
                />
              </div>

              {error ? (
                <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
                  {error}
                </p>
              ) : null}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full rounded-xl border border-violet-400/30 bg-violet-500/18 px-4 py-2.5 text-sm font-medium text-violet-100 transition-colors hover:bg-violet-500/25 disabled:opacity-50"
              >
                {isSubmitting ? "Please wait..." : "Request reset"}
              </button>

              <Link href="/auth/signin" className="block text-center text-sm text-zinc-400 hover:text-zinc-200">
                Back to sign in
              </Link>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
