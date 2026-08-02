export type LeadStatus = "PENDING" | "REACHED_OUT";

export type Lead = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  resume_filename: string;
  resume_content_type: string;
  status: LeadStatus;
  created_at: string;
  updated_at: string;
  resume_url?: string | null;
  reached_out_by?: string | null;
  reached_out_by_email?: string | null;
  reached_out_at?: string | null;
};

export type LeadListResponse = {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function authHeaders(token?: string | null): HeadersInit {
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

async function readError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
    return JSON.stringify(data);
  } catch {
    return (await response.text()) || "Request failed";
  }
}

export async function submitLead(formData: FormData): Promise<Lead> {
  const response = await fetch(`${API_BASE}/api/v1/leads`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json();
}

export async function listLeads(
  token: string,
  page = 1,
  pageSize = 20,
): Promise<LeadListResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  const response = await fetch(`${API_BASE}/api/v1/leads?${params}`, {
    headers: authHeaders(token),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json();
}

export async function markReachedOut(token: string, leadId: string): Promise<Lead> {
  const response = await fetch(`${API_BASE}/api/v1/leads/${leadId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(token),
    },
    body: JSON.stringify({ status: "REACHED_OUT" }),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json();
}

export function resolveResumeUrl(resumeUrl: string | null | undefined): string | null {
  if (!resumeUrl) return null;
  if (resumeUrl.startsWith("http")) return resumeUrl;
  return `${API_BASE}${resumeUrl}`;
}

export { API_BASE };
