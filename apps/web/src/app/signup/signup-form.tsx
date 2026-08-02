"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

export default function SignupForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = searchParams.get("next") || "/admin/leads";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
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
    setInfo(null);

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      setLoading(false);
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      setLoading(false);
      return;
    }
    if (!canUseSupabase) {
      setError("Supabase Auth is not configured — signup is unavailable.");
      setLoading(false);
      return;
    }

    try {
      const supabase = createClient();
      const origin = typeof window !== "undefined" ? window.location.origin : undefined;
      const { data, error: signUpError } = await supabase.auth.signUp({
        email,
        password,
        options: origin
          ? {
              emailRedirectTo: `${origin}/admin/leads`,
            }
          : undefined,
      });
      if (signUpError) {
        setError(signUpError.message);
        return;
      }

      // Supabase returns a user with empty identities when the email is already registered
      // and "Confirm email" is enabled (anti-enumeration). Treat as success messaging.
      if (data.user && Array.isArray(data.user.identities) && data.user.identities.length === 0) {
        setInfo("If this email is new, check your inbox to confirm. Otherwise sign in.");
        return;
      }

      if (data.session) {
        router.push(nextPath);
        router.refresh();
        return;
      }

      setInfo("Account created. Check your email to confirm, then sign in.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
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
        Attorney signup
      </h1>
      <p className="mt-2 text-[var(--ink-soft)]">
        Create an account to access the shared leads inbox.
      </p>

      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        <label className="block space-y-1.5 text-sm">
          <span className="font-medium text-[var(--ink-soft)]">Email</span>
          <input
            required
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none focus:border-[var(--accent)]"
          />
        </label>
        <label className="block space-y-1.5 text-sm">
          <span className="font-medium text-[var(--ink-soft)]">Password</span>
          <input
            required
            type="password"
            autoComplete="new-password"
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none focus:border-[var(--accent)]"
          />
        </label>
        <label className="block space-y-1.5 text-sm">
          <span className="font-medium text-[var(--ink-soft)]">Confirm password</span>
          <input
            required
            type="password"
            autoComplete="new-password"
            minLength={6}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none focus:border-[var(--accent)]"
          />
        </label>
        {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}
        {info ? <p className="text-sm text-[var(--accent-deep)]">{info}</p> : null}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-[var(--ink)] px-4 py-3 font-semibold text-[var(--paper)] transition hover:bg-[var(--accent)] disabled:opacity-60"
        >
          {loading ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="mt-6 text-sm text-[var(--ink-soft)]">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-[var(--accent)] hover:underline">
          Sign in
        </Link>
      </p>
    </main>
  );
}
