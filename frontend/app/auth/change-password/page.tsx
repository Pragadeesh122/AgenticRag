"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/AuthProvider";
import { changePassword } from "@/lib/api";

export default function ChangePasswordPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/auth/signin");
    }
  }, [isLoading, router, user]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setIsSubmitting(true);
    try {
      await changePassword(currentPassword, newPassword);
      setSubmitted(true);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to change password";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading || !user) {
    return (
      <div className="relative flex h-screen w-screen flex-col items-center justify-center overflow-hidden bg-[#131417] text-zinc-200">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(124,58,237,0.18),transparent_30%),radial-gradient(circle_at_80%_10%,rgba(34,197,94,0.14),transparent_28%),radial-gradient(circle_at_40%_90%,rgba(59,130,246,0.12),transparent_32%)]" />
        <div className="relative z-10 flex flex-col items-center gap-3 rounded-2xl border border-white/10 bg-[#1b1d21]/90 px-8 py-7 backdrop-blur">
          <div className="h-9 w-9 rounded-full border-2 border-zinc-700 border-t-violet-400 animate-spin" />
          <p className="text-sm text-zinc-300">Loading account settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#131417] text-zinc-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(124,58,237,0.18),transparent_30%),radial-gradient(circle_at_80%_10%,rgba(34,197,94,0.14),transparent_28%),radial-gradient(circle_at_40%_90%,rgba(59,130,246,0.12),transparent_32%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-[0.08] [background-image:linear-gradient(to_right,#ffffff_1px,transparent_1px),linear-gradient(to_bottom,#ffffff_1px,transparent_1px)] [background-size:42px_42px]" />

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-lg items-center px-6 py-10">
        <div className="w-full rounded-2xl border border-white/10 bg-[#1b1d21]/95 p-7 shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-100">
            Change password
          </h1>
          <p className="mt-2 text-sm text-zinc-400">
            Update the password for your credentials-based account.
          </p>

          {submitted ? (
            <div className="mt-5 space-y-3">
              <p className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
                Your password has been updated.
              </p>
              <Link href="/chat" className="text-sm text-violet-300 hover:text-violet-200">
                Return to chat
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="mt-5 space-y-4">
              <div>
                <label htmlFor="current-password" className="mb-1.5 block text-sm font-medium text-zinc-300">
                  Current password
                </label>
                <input
                  id="current-password"
                  type="password"
                  value={currentPassword}
                  onChange={(event) => setCurrentPassword(event.target.value)}
                  autoComplete="current-password"
                  required
                  className="w-full rounded-xl border border-white/10 bg-black/25 px-3 py-2.5 text-sm text-zinc-100 outline-none transition-colors placeholder:text-zinc-500 focus:border-violet-400/60"
                />
              </div>

              <div>
                <label htmlFor="new-password" className="mb-1.5 block text-sm font-medium text-zinc-300">
                  New password
                </label>
                <input
                  id="new-password"
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  autoComplete="new-password"
                  minLength={8}
                  required
                  className="w-full rounded-xl border border-white/10 bg-black/25 px-3 py-2.5 text-sm text-zinc-100 outline-none transition-colors placeholder:text-zinc-500 focus:border-violet-400/60"
                />
              </div>

              <div>
                <label htmlFor="confirm-password" className="mb-1.5 block text-sm font-medium text-zinc-300">
                  Confirm new password
                </label>
                <input
                  id="confirm-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  autoComplete="new-password"
                  minLength={8}
                  required
                  className="w-full rounded-xl border border-white/10 bg-black/25 px-3 py-2.5 text-sm text-zinc-100 outline-none transition-colors placeholder:text-zinc-500 focus:border-violet-400/60"
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
                {isSubmitting ? "Please wait..." : "Change password"}
              </button>

              <Link href="/chat" className="block text-center text-sm text-zinc-400 hover:text-zinc-200">
                Back to chat
              </Link>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
