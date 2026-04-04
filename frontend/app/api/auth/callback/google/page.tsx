"use client";

import { useEffect, useState, Suspense, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function CallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshUser } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const processStarted = useRef(false);
  const code = searchParams.get("code");
  const state = searchParams.get("state");
  const missingParams = !code || !state;

  useEffect(() => {
    if (missingParams) return;

    if (processStarted.current) return;
    processStarted.current = true;

    const processCallback = async () => {
      try {
        // Exchange code/state with fastapi-users backend
        // Note: the fastapi-users oauth callback relies on GET request taking `code` and `state`.
        const res = await fetch(`${API_BASE_URL}/auth/google/callback?code=${code}&state=${state}`, {
           credentials: "include" // ensure we accept the Set-Cookie JWT from backend!
        });

        if (res.ok) {
          // Cookie is securely set. Refresh auth and redirect.
          await refreshUser();
          router.push("/chat");
        } else {
          setError(`Authentication failed with status: ${res.status}`);
        }
      } catch (err) {
        console.error(err);
        setError("Network error while verifying OAuth callback.");
      }
    };

    processCallback();
  }, [code, state, missingParams, router, refreshUser]);

  if (missingParams) {
    return (
      <div className="flex h-screen w-screen flex-col items-center justify-center bg-[#1a1a1a] text-zinc-100">
        <h2 className="mb-4 text-2xl font-bold">Authentication Error</h2>
        <p className="mb-6 text-red-400">Missing authorization parameters from Google.</p>
        <button
          onClick={() => router.push("/auth/signin")}
          className="rounded-lg bg-zinc-800 px-4 py-2 text-sm font-medium hover:bg-zinc-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen w-screen flex-col items-center justify-center bg-[#1a1a1a] text-zinc-100">
        <h2 className="text-2xl font-bold mb-4">Authentication Error</h2>
        <p className="text-red-400 mb-6">{error}</p>
        <button 
          onClick={() => router.push("/auth/signin")}
          className="rounded-lg bg-zinc-800 px-4 py-2 text-sm font-medium hover:bg-zinc-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen w-screen items-center justify-center bg-[#1a1a1a] text-zinc-300">
      <div className="mb-4 h-8 w-8 rounded-full border-2 border-zinc-700 border-t-violet-500 animate-spin" />
      <p>Verifying Google Login...</p>
    </div>
  );
}

export default function CallbackPage() {
  return (
    <Suspense fallback={
       <div className="flex flex-col h-screen items-center justify-center bg-[#1a1a1a] text-zinc-300">
          Loading...
       </div>
    }>
      <CallbackHandler />
    </Suspense>
  );
}
