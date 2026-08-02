"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Lead,
  listLeads,
  markReachedOut,
  resolveResumeUrl,
} from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

async function getAccessToken(): Promise<string | null> {
  if (process.env.NEXT_PUBLIC_DEV_AUTH_BYPASS === "true") {
    const dev = localStorage.getItem("leads_dev_token");
    if (dev) return dev;
  }
  try {
    const supabase = createClient();
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  } catch {
    return localStorage.getItem("leads_dev_token");
  }
}

export default function AdminLeadsPage() {
  const router = useRouter();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = await getAccessToken();
      if (!token) {
        router.push("/login?next=/admin/leads");
        return;
      }
      const data = await listLeads(token);
      setLeads(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load leads");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onMarkReachedOut(leadId: string) {
    setUpdatingId(leadId);
    try {
      const token = await getAccessToken();
      if (!token) return;
      const updated = await markReachedOut(token, leadId);
      setLeads((current) => current.map((lead) => (lead.id === leadId ? updated : lead)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setUpdatingId(null);
    }
  }

  async function onSignOut() {
    localStorage.removeItem("leads_dev_token");
    try {
      const supabase = createClient();
      await supabase.auth.signOut();
    } catch {
      // ignore when Supabase is not configured
    }
    router.push("/login");
  }

  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl px-6 py-10">
      <header className="mb-10 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.14em] text-[var(--ink-soft)]">
            Northbridge
          </p>
          <h1
            className="mt-1 text-4xl tracking-tight"
            style={{ fontFamily: "var(--font-display), Georgia, serif" }}
          >
            Leads
          </h1>
          <p className="mt-2 text-[var(--ink-soft)]">
            {total} prospect{total === 1 ? "" : "s"} in the pipeline
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => void load()}
            className="rounded-xl border border-[var(--line)] bg-white/70 px-4 py-2 text-sm font-medium"
          >
            Refresh
          </button>
          <Link href="/" className="text-sm text-[var(--ink-soft)] hover:text-[var(--accent)]">
            Public form
          </Link>
          <button
            type="button"
            onClick={() => void onSignOut()}
            className="text-sm text-[var(--ink-soft)] hover:text-[var(--danger)]"
          >
            Sign out
          </button>
        </div>
      </header>

      {error ? <p className="mb-4 text-sm text-[var(--danger)]">{error}</p> : null}
      {loading ? (
        <p className="text-[var(--ink-soft)]">Loading leads…</p>
      ) : leads.length === 0 ? (
        <p className="rounded-2xl border border-dashed border-[var(--line)] bg-white/50 px-6 py-16 text-center text-[var(--ink-soft)]">
          No leads yet. Share the public form to collect the first submission.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-[var(--line)] bg-[rgba(255,252,246,0.8)]">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-[var(--line)] text-[var(--ink-soft)]">
              <tr>
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">Resume</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Submitted</th>
                <th className="px-4 py-3 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => {
                return (
                  <tr key={lead.id} className="border-b border-[var(--line)] last:border-0">
                    <td className="px-4 py-3 font-medium">
                      {lead.first_name} {lead.last_name}
                    </td>
                    <td className="px-4 py-3">
                      <a className="hover:text-[var(--accent)]" href={`mailto:${lead.email}`}>
                        {lead.email}
                      </a>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        className="font-medium text-[var(--accent)] hover:underline"
                        onClick={async () => {
                          const token = await getAccessToken();
                          if (!token) return;
                          const detailRes = await fetch(
                            `${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/api/v1/leads/${lead.id}`,
                            { headers: { Authorization: `Bearer ${token}` } },
                          );
                          if (!detailRes.ok) return;
                          const detail = (await detailRes.json()) as Lead;
                          const href = resolveResumeUrl(detail.resume_url);
                          if (!href) return;
                          if (href.startsWith("http") && !href.includes("/api/v1/leads/files/")) {
                            window.open(href, "_blank", "noopener,noreferrer");
                            return;
                          }
                          const fileRes = await fetch(href, {
                            headers: { Authorization: `Bearer ${token}` },
                          });
                          if (!fileRes.ok) return;
                          const blob = await fileRes.blob();
                          const objectUrl = URL.createObjectURL(blob);
                          window.open(objectUrl, "_blank", "noopener,noreferrer");
                        }}
                      >
                        {lead.resume_filename}
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold"
                        style={{
                          background:
                            lead.status === "PENDING"
                              ? "rgba(138,90,0,0.12)"
                              : "rgba(15,110,86,0.12)",
                          color: lead.status === "PENDING" ? "var(--pending)" : "var(--reached)",
                        }}
                      >
                        {lead.status === "PENDING" ? "Pending" : "Reached out"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-[var(--ink-soft)]">
                      {new Date(lead.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      {lead.status === "PENDING" ? (
                        <button
                          type="button"
                          disabled={updatingId === lead.id}
                          onClick={() => void onMarkReachedOut(lead.id)}
                          className="rounded-lg bg-[var(--ink)] px-3 py-1.5 text-xs font-semibold text-[var(--paper)] disabled:opacity-50"
                        >
                          {updatingId === lead.id ? "Saving…" : "Mark reached out"}
                        </button>
                      ) : (
                        <span className="text-xs text-[var(--ink-soft)]">Done</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
