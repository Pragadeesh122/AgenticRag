"use client";

import { useState } from "react";
import { GoogleLogo } from "@phosphor-icons/react/dist/ssr/GoogleLogo";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import { redirect } from "next/navigation";

export default function SignIn() {
  const { user, isLoading } = useAuth();
  const [loading, setLoading] = useState(false);

  if (user && !isLoading) {
    redirect("/chat");
  }

  const handleGoogleLogin = async () => {
    setLoading(true);
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

  return (
    <div className="flex h-screen items-center justify-center bg-[#1a1a1a]">
      <div className="w-full max-w-sm rounded-xl border border-zinc-800 bg-[#222] p-8 shadow-xl">
        <h1 className="mb-2 text-center text-2xl font-bold text-zinc-100">Welcome Back</h1>
        <p className="mb-8 text-center text-sm text-zinc-400">Sign in to your account</p>
        
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
