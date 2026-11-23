const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001";

export type ProfilePayload = {
  full_name: string;
  email?: string | null;
  career?: string | null;
  cycle?: number | null;
  location?: string | null;
  target_roles?: string[];
  locale?: string;
};

export type Profile = ProfilePayload & {
  id: string;
  phone: string | null;
  university: string | null;
  preferred_modality: string | null;
  salary_expectation: number | null;
  availability: string | null;
  created_at: string;
  updated_at: string;
};

export type CVSkill = {
  skill_id: string;
  canonical_name: string;
  category: string;
  level: number;
  evidence: string | null;
  confidence: number | null;
  confirmed: boolean;
};

export type CVResult = {
  cv_id: string;
  filename: string;
  mime_type: string;
  raw_text: string;
  sections: Record<string, string>;
  skills: CVSkill[];
  contact: { email: string | null; phone: string | null };
  warnings: string[];
  redacted_text: string;
};

export type AIResult = {
  provider: string;
  redacted_text: string;
  pii_removed: boolean;
  suggestions: string[];
};

export type Offer = {
  id: string;
  source_type: string;
  external_id: string | null;
  source_url: string | null;
  captured_at: string;
  title: string;
  company: string;
  location: string | null;
  modality: string | null;
  salary_text: string | null;
  salary_amount: number | null;
  salary_currency: string | null;
  description: string | null;
  requirements_text: string | null;
  published_at: string | null;
  deadline_at: string | null;
  parse_confidence: number | null;
  dedupe_hash: string | null;
};

export type OfferMutation = {
  offer: Offer;
  duplicate: boolean;
};

export type OfferImportResult = {
  created: number;
  duplicates: number;
  errors: Array<{ row: number; message: string; details: Record<string, unknown> }>;
  warnings: string[];
  total_rows: number;
  preview: Array<{
    title: string;
    company: string;
    salary_amount: number | null;
    source_url: string | null;
    duplicate: boolean;
  }>;
  offer_ids: string[];
};

export type MCPSearchResult = {
  results: Array<{
    titulo: string;
    empresa: string;
    ubicacion?: string;
    subvencion?: string;
    modalidad?: string;
    vence?: string;
    url: string;
    id_oferta?: string;
  }>;
  total: number;
  warning: string | null;
};

export type SourceStatus = {
  mcp: "available" | "unavailable" | string;
  detail: string | null;
  filters: Record<string, unknown> | null;
};

export type OfferPayload = {
  title: string;
  company: string;
  source_url?: string | null;
  location?: string | null;
  modality?: string | null;
  salary_text?: string | null;
  salary_amount?: number | null;
  description?: string | null;
  requirements_text?: string | null;
  deadline_at?: string | null;
};

export type BookmarkletPayload = {
  url: string;
  title?: string;
  company?: string;
  location?: string;
  salary_text?: string;
  og_site_name?: string;
  jsonld: string[];
  text: string;
};

export type BookmarkletPreview = {
  title: string;
  company: string;
  source_url: string;
  location: string | null;
  modality: string | null;
  salary_text: string | null;
  salary_amount: number | null;
  salary_currency: string | null;
  description: string | null;
  requirements_text: string | null;
  published_at: string | null;
  deadline_at: string | null;
  confidence: number;
  warnings: string[];
};

export type EmailCandidate = {
  url: string;
  title: string;
  source: string;
};

export type EmailPreview = {
  subject: string;
  candidates: EmailCandidate[];
  warnings: string[];
};

export type PractilizateStatus = {
  enabled: boolean;
  detail: string;
};



export type Match = {
  id: string;
  profile_id: string;
  offer_id: string;
  overall_score: number;
  must_have_score: number;
  confidence: number;
  decision: "apply" | "apply_with_gaps" | "improve_cv";
  gaps_json: Array<{
    skill: string;
    requirement_type: string;
    required_level: number;
    user_level: number;
    evidence: string | null;
    suggestion: string;
  }>;
  explanation_json: Array<{
    skill: string;
    requirement_type: string;
    required_level: number;
    user_level: number;
    status: string;
    evidence: string | null;
    suggestion: string | null;
  }>;
  overridden: boolean;
  override_reason: string | null;
  created_at: string;
};

export type Application = {
  id: string;
  profile_id: string;
  offer_id: string;
  status: "saved" | "applied" | "interview" | "rejected" | "offer";
  applied_at: string | null;
  next_action_at: string | null;
  next_action_note: string | null;
  notes: string | null;
  cv_document_id: string | null;
  created_at: string;
  updated_at: string;
};

export type ApplicationWithOffer = {
  application: Application;
  offer: Offer;
  match: Match | null;
};

export type Reminder = {
  id: string;
  application_id: string;
  due_at: string;
  channel: string;
  message: string | null;
  status: string;
};

export type ApplicationEvent = {
  id: string;
  application_id: string;
  event_type: string;
  event_at: string;
  notes: string | null;
};



async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init);
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const message =
      payload?.error?.message ?? payload?.detail?.[0]?.msg ?? `Request failed: ${response.status}`;
    throw new Error(message);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function createProfile(payload: ProfilePayload): Promise<Profile> {
  return request<Profile>("/api/v1/profiles", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getProfile(profileId: string): Promise<Profile> {
  return request<Profile>(`/api/v1/profiles/${profileId}`);
}

export async function updateProfile(
  profileId: string,
  payload: Partial<ProfilePayload>,
): Promise<Profile> {
  return request<Profile>(`/api/v1/profiles/${profileId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function uploadCV(profileId: string, file: File): Promise<CVResult> {
  const form = new FormData();
  form.append("file", file);
  return request<CVResult>(`/api/v1/profiles/${profileId}/cv`, {
    method: "POST",
    body: form,
  });
}

export async function updateSkills(
  profileId: string,
  skills: Array<Pick<CVSkill, "skill_id" | "level" | "evidence" | "confirmed">>,
): Promise<{ skills: CVSkill[] }> {
  return request<{ skills: CVSkill[] }>(`/api/v1/profiles/${profileId}/cv/skills`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ skills }),
  });
}

export async function analyzeCV(
  profileId: string,
  text: string,
  consent: boolean,
): Promise<AIResult> {
  return request<AIResult>(`/api/v1/profiles/${profileId}/cv/analyze-ai`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, consent }),
  });
}

export async function createOffer(payload: OfferPayload): Promise<OfferMutation> {
  return request<OfferMutation>("/api/v1/offers/manual", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function importOffersCsv(file: File): Promise<OfferImportResult> {
  const form = new FormData();
  form.append("file", file);
  return request<OfferImportResult>("/api/v1/offers/import/csv", {
    method: "POST",
    body: form,
  });
}

export async function previewEmailAlerts(file: File): Promise<EmailPreview> {
  const form = new FormData();
  form.append("file", file);
  return request<EmailPreview>("/api/v1/offers/import/email/preview", {
    method: "POST",
    body: form,
  });
}

export async function importEmailAlerts(urls: string[]): Promise<OfferImportResult> {
  return request<OfferImportResult>("/api/v1/offers/import/email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ urls }),
  });
}

export async function getPractilizateStatus(): Promise<PractilizateStatus> {
  return request<PractilizateStatus>("/api/v1/offers/sources/practilizate/status");
}

export async function importPractilizateCsv(file: File): Promise<OfferImportResult> {
  const form = new FormData();
  form.append("file", file);
  return request<OfferImportResult>("/api/v1/offers/import/practilizate", {
    method: "POST",
    body: form,
  });
}

export async function captureOfferUrl(url: string): Promise<OfferMutation> {
  return request<OfferMutation>("/api/v1/offers/capture-url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
}

export async function previewBookmarklet(
  payload: BookmarkletPayload,
): Promise<BookmarkletPreview> {
  return request<BookmarkletPreview>("/api/v1/offers/bookmarklet/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function createBookmarkletOffer(
  payload: OfferPayload,
): Promise<OfferMutation> {
  return request<OfferMutation>("/api/v1/offers/bookmarklet", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function searchMCP(payload: {
  q?: string;
  modality?: string;
  career?: string;
  department?: string;
  limit?: number;
}): Promise<MCPSearchResult> {
  return request<MCPSearchResult>("/api/v1/offers/mcp/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function importMCP(urls: string[]): Promise<OfferImportResult> {
  return request<OfferImportResult>("/api/v1/offers/mcp/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ urls }),
  });
}

export async function listOffers(sourceType?: string): Promise<Offer[]> {
  const query = sourceType ? `?source_type=${encodeURIComponent(sourceType)}` : "";
  return request<Offer[]>(`/api/v1/offers${query}`);
}

export async function getSourceStatus(): Promise<SourceStatus> {
  return request<SourceStatus>("/api/v1/offers/sources/status");
}

export async function getOffer(offerId: string): Promise<Offer> {
  return request<Offer>(`/api/v1/offers/${offerId}`);
}

export async function createMatch(profileId: string, offerId: string): Promise<Match> {
  return request<Match>("/api/v1/matches", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile_id: profileId, offer_id: offerId }),
  });
}

export async function overrideMatch(
  matchId: string,
  decision: Match["decision"],
  reason: string | null,
): Promise<Match> {
  return request<Match>(`/api/v1/matches/${matchId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, reason }),
  });
}

export async function createApplication(payload: {
  profile_id: string;
  offer_id: string;
  status?: Application["status"];
  next_action_at?: string | null;
  next_action_note?: string | null;
  notes?: string | null;
}): Promise<{ application: Application; duplicate: boolean }> {
  return request<{ application: Application; duplicate: boolean }>("/api/v1/applications", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function listApplications(profileId: string): Promise<ApplicationWithOffer[]> {
  return request<ApplicationWithOffer[]>(
    `/api/v1/applications?profile_id=${encodeURIComponent(profileId)}`,
  );
}

export async function updateApplication(
  applicationId: string,
  payload: Partial<Pick<Application, "status" | "next_action_at" | "next_action_note" | "notes">>,
): Promise<Application> {
  return request<Application>(`/api/v1/applications/${applicationId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function addReminder(
  applicationId: string,
  payload: { due_at: string; channel?: string; message?: string | null },
): Promise<Reminder> {
  return request<Reminder>(`/api/v1/applications/${applicationId}/reminders`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function listReminders(applicationId: string): Promise<Reminder[]> {
  return request<Reminder[]>(`/api/v1/applications/${applicationId}/reminders`);
}

export async function addApplicationEvent(
  applicationId: string,
  payload: { event_type: string; event_at: string; notes?: string | null },
): Promise<ApplicationEvent> {
  return request<ApplicationEvent>(`/api/v1/applications/${applicationId}/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function exportUrl(
  kind: "applications.xlsx" | "applications.csv" | "calendar.ics",
  profileId: string,
): string {
  return `${API_URL}/api/v1/exports/${kind}?profile_id=${encodeURIComponent(profileId)}`;
}


