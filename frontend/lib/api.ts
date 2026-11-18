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
