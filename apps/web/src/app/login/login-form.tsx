"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

/** Only allow same-origin admin paths — blocks //evil and absolute URLs. */
function safeNextPath(raw: string | null): string {
  if (!raw) return "/admin/leads";
  if (!raw.startsWith("/")) return "/admin/leads";
  if (raw.startsWith("//") || raw.includes("://")) return "/admin/leads";
  if (!raw.startsWith("/admin")) return "/admin/leads";
  return raw;
}

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = safeNextPath(searchParams.get("next"));
  const useDevAuth = process.env.NEXT_PUBLIC_DEV_AUTH_BYPASS === "true";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const canUseSupabase = useMemo(() => {
    return Boolean(
      process.env.NEXT_PUBLIC_SUPABASE_URL &&
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY &&
        !process.env.NEXT_PUBLIC_SUPABASE_URL.includes("YOUR_PROJECT"),
    );
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (useDevAuth && !canUseSupabase) {
        localStorage.setItem("leads_dev_token", "dev-token");
        router.push(nextPath);
        return;
      }

      const supabase = createClient();
      const { error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (signInError) {
        setError(signInError.message);
        return;
      }
      router.push(nextPath);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-6 py-16">
      <Link href="/" className="mb-10 text-sm text-[var(--ink-soft)] hover:text-[var(--accent)]">
        ← Back to Northbridge
      </Link>
      <h1
        className="text-4xl tracking-tight"
        style={{ fontFamily: "var(--font-display), Georgia, serif" }}
      >
        Attorney login
      </h1>
      <p className="mt-2 text-[var(--ink-soft)]">
        {useDevAuth && !canUseSupabase
          ? "Dev auth is on — continue to open the admin console."
          : "Sign in with your Supabase attorney account."}
      </p>

      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        {canUseSupabase || !useDevAuth ? (
          <>
            <label className="block space-y-1.5 text-sm">
              <span className="font-medium text-[var(--ink-soft)]">Email</span>
              <input
                required={!useDevAuth}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none focus:border-[var(--accent)]"
              />
            </label>
            <label className="block space-y-1.5 text-sm">
              <span className="font-medium text-[var(--ink-soft)]">Password</span>
              <input
                required={!useDevAuth}
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none focus:border-[var(--accent)]"
              />
            </label>
          </>
        ) : null}
        {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-[var(--ink)] px-4 py-3 font-semibold text-[var(--paper)] transition hover:bg-[var(--accent)] disabled:opacity-60"
        >
          {loading ? "Signing in…" : useDevAuth && !canUseSupabase ? "Enter admin" : "Sign in"}
        </button>
      </form>
    </main>
  );
}
