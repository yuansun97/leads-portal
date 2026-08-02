"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { submitLead } from "@/lib/api";

export default function HomePage() {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await submitLead(data);
      setDone(true);
      form.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            "linear-gradient(rgba(20,33,43,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(20,33,43,0.04) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage: "radial-gradient(ellipse at center, black 30%, transparent 75%)",
        }}
      />

      <header className="relative mx-auto flex w-full max-w-5xl items-center justify-between px-6 pb-8 pt-8">
        <p
          className="text-2xl tracking-tight text-[var(--ink)] md:text-3xl"
          style={{ fontFamily: "var(--font-display), Georgia, serif" }}
        >
          Northbridge
        </p>
        <Link
          href="/login"
          className="text-sm font-medium text-[var(--ink-soft)] transition hover:text-[var(--accent)]"
        >
          Attorney login
        </Link>
      </header>

      <section className="relative mx-auto grid w-full max-w-5xl gap-10 px-6 pb-20 pt-4 md:grid-cols-[1.1fr_0.9fr] md:items-end md:gap-16 md:pb-28 md:pt-10">
        <div className="max-w-xl">
          <h1
            className="text-5xl leading-[1.05] tracking-tight text-[var(--ink)] md:text-6xl"
            style={{ fontFamily: "var(--font-display), Georgia, serif" }}
          >
            Tell us about your matter.
          </h1>
          <p className="mt-5 max-w-md text-lg leading-relaxed text-[var(--ink-soft)]">
            Share your details and resume. Our attorneys will review and reach out.
          </p>
        </div>

        <div className="relative">
          <div
            aria-hidden
            className="absolute -inset-6 -z-10 rounded-[2rem] bg-[var(--accent)]/10 blur-2xl"
          />
          <form
            onSubmit={onSubmit}
            className="rounded-[1.5rem] border border-[var(--line)] bg-[rgba(255,252,246,0.88)] p-6 shadow-[0_24px_60px_rgba(20,33,43,0.08)] backdrop-blur md:p-8"
          >
            {done ? (
              <div className="space-y-3 py-6 text-center">
                <p
                  className="text-3xl text-[var(--ink)]"
                  style={{ fontFamily: "var(--font-display), Georgia, serif" }}
                >
                  Received.
                </p>
                <p className="text-[var(--ink-soft)]">
                  Check your email for a confirmation. An attorney will follow up soon.
                </p>
                <button
                  type="button"
                  className="mt-4 text-sm font-semibold text-[var(--accent)]"
                  onClick={() => setDone(false)}
                >
                  Submit another
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="block space-y-1.5 text-sm">
                    <span className="font-medium text-[var(--ink-soft)]">First name</span>
                    <input
                      required
                      name="first_name"
                      className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none transition focus:border-[var(--accent)]"
                    />
                  </label>
                  <label className="block space-y-1.5 text-sm">
                    <span className="font-medium text-[var(--ink-soft)]">Last name</span>
                    <input
                      required
                      name="last_name"
                      className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none transition focus:border-[var(--accent)]"
                    />
                  </label>
                </div>
                <label className="block space-y-1.5 text-sm">
                  <span className="font-medium text-[var(--ink-soft)]">Email</span>
                  <input
                    required
                    type="email"
                    name="email"
                    className="w-full rounded-xl border border-[var(--line)] bg-white/80 px-3 py-2.5 outline-none transition focus:border-[var(--accent)]"
                  />
                </label>
                <label className="block space-y-1.5 text-sm">
                  <span className="font-medium text-[var(--ink-soft)]">Resume / CV</span>
                  <input
                    required
                    type="file"
                    name="resume"
                    accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    className="w-full rounded-xl border border-dashed border-[var(--line)] bg-white/60 px-3 py-3 file:mr-3 file:rounded-lg file:border-0 file:bg-[var(--paper-deep)] file:px-3 file:py-1.5 file:text-sm"
                  />
                </label>
                {error ? (
                  <p className="text-sm text-[var(--danger)]">{error}</p>
                ) : null}
                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full rounded-xl bg-[var(--accent)] px-4 py-3 font-semibold text-white transition hover:bg-[var(--accent-deep)] disabled:opacity-60"
                >
                  {submitting ? "Submitting…" : "Submit application"}
                </button>
              </div>
            )}
          </form>
        </div>
      </section>
    </main>
  );
}
