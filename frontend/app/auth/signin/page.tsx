"use client";

import { useState, type FormEvent } from "react";
import { GoogleLogo } from "@phosphor-icons/react/dist/ssr/GoogleLogo";
import { apiFetch, loginWithCredentials, registerWithCredentials } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import { redirect } from "next/navigation";

export default function SignIn() {
  const { user, isLoading, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [authMode, setAuthMode] = useState<"signin" | "register">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (user && !isLoading) {
    redirect("/chat");
  }

  const handleGoogleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch("/auth/google/authorize");
      if (res.ok) {
        const data = await res.json();
        // Redirect user to Google OAuth page
        window.location.href = data.authorization_url;
      } else {
        console.error("Failed to get Google authorization URL");
        setLoading(false);
      }
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  const handleCredentialsAuth = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (authMode === "register") {
        await registerWithCredentials(email.trim(), password);
      }

      await loginWithCredentials(email.trim(), password);
      await refreshUser();
      window.location.href = "/chat";
    } catch (err) {
      const message = err instanceof Error ? err.message : "Authentication failed";
      setError(message);
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-[#1a1a1a]">
      <div className="w-full max-w-sm rounded-xl border border-zinc-800 bg-[#222] p-8 shadow-xl">
        <h1 className="mb-2 text-center text-2xl font-bold text-zinc-100">Welcome Back</h1>
        <p className="mb-6 text-center text-sm text-zinc-400">Sign in to your account</p>

        <div className="mb-6 grid grid-cols-2 rounded-lg border border-zinc-800 bg-zinc-900/60 p-1">
          <button
            type="button"
            onClick={() => {
              setAuthMode("signin");
              setError(null);
            }}
            className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              authMode === "signin" ? "bg-zinc-100 text-zinc-900" : "text-zinc-400 hover:text-zinc-100"
            }`}
          >
            Sign in
          </button>
          <button
            type="button"
            onClick={() => {
              setAuthMode("register");
              setError(null);
            }}
            className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              authMode === "register" ? "bg-zinc-100 text-zinc-900" : "text-zinc-400 hover:text-zinc-100"
            }`}
          >
            Create account
          </button>
        </div>

        <form onSubmit={handleCredentialsAuth} className="space-y-4">
          <div>
            <label htmlFor="email" className="mb-2 block text-sm font-medium text-zinc-300">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2.5 text-sm text-zinc-100 outline-none transition-colors placeholder:text-zinc-500 focus:border-zinc-500"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-2 block text-sm font-medium text-zinc-300">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete={authMode === "signin" ? "current-password" : "new-password"}
              required
              minLength={8}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2.5 text-sm text-zinc-100 outline-none transition-colors placeholder:text-zinc-500 focus:border-zinc-500"
              placeholder="At least 8 characters"
            />
          </div>

          {error ? <p className="text-sm text-red-400">{error}</p> : null}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-zinc-100 px-4 py-2.5 text-sm font-medium text-zinc-900 transition-colors hover:bg-white disabled:opacity-50"
          >
            {loading ? "Please wait..." : authMode === "signin" ? "Sign in with email" : "Create account"}
          </button>
        </form>

        <div className="my-6 flex items-center gap-3">
          <div className="h-px flex-1 bg-zinc-800" />
          <span className="text-xs uppercase tracking-[0.2em] text-zinc-500">or</span>
          <div className="h-px flex-1 bg-zinc-800" />
        </div>

        <button
          onClick={handleGoogleLogin}
          disabled={loading}
          className="flex w-full items-center justify-center gap-3 rounded-lg bg-zinc-100 px-4 py-2.5 text-sm font-medium text-zinc-900 transition-colors hover:bg-white disabled:opacity-50"
        >
          {loading ? (
             <div className="h-5 w-5 rounded-full border-2 border-zinc-500 border-t-zinc-900 animate-spin" />
          ) : (
            <>
              <GoogleLogo size={20} weight="fill" />
              Continue with Google
            </>
          )}
        </button>
      </div>
    </div>
  );
}
