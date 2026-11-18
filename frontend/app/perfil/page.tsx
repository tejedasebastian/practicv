"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  analyzeCV,
  createProfile,
  getProfile,
  updateProfile,
  updateSkills,
  uploadCV,
  type AIResult,
  type CVResult,
  type CVSkill,
} from "@/lib/api";
import { dictionaries, type Locale } from "@/lib/i18n";

type FormState = {
  full_name: string;
  email: string;
  career: string;
  cycle: string;
  location: string;
  target_roles: string;
};

const emptyForm: FormState = {
  full_name: "",
  email: "",
  career: "",
  cycle: "",
  location: "",
  target_roles: "",
};

export default function ProfilePage() {
  const [locale, setLocale] = useState<Locale>("es");
  const t = dictionaries[locale].profile;
  const [profileId, setProfileId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [file, setFile] = useState<File | null>(null);
  const [cv, setCv] = useState<CVResult | null>(null);
  const [skills, setSkills] = useState<CVSkill[]>([]);
  const [consent, setConsent] = useState(false);
  const [ai, setAi] = useState<AIResult | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  useEffect(() => {
    const saved = window.localStorage.getItem("practicv.profileId");
    if (!saved) return;
    setProfileId(saved);
    getProfile(saved)
      .then((profile) => {
        setForm({
          full_name: profile.full_name,
          email: profile.email ?? "",
          career: profile.career ?? "",
          cycle: profile.cycle ? String(profile.cycle) : "",
          location: profile.location ?? "",
          target_roles: (profile.target_roles ?? []).join(", "),
        });
      })
      .catch(() => undefined);
  }, []);

  function updateForm(field: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSaveProfile() {
    setBusy("profile");
    setError(null);
    setStatus(null);
    try {
      const payload = {
        full_name: form.full_name,
        email: form.email || null,
        career: form.career || null,
        cycle: form.cycle ? Number(form.cycle) : null,
        location: form.location || null,
        target_roles: form.target_roles
          .split(",")
          .map((role) => role.trim())
          .filter(Boolean),
        locale,
      };
      const saved = profileId
        ? await updateProfile(profileId, payload)
        : await createProfile(payload);
      setProfileId(saved.id);
      window.localStorage.setItem("practicv.profileId", saved.id);
      setStatus(t.profileSaved);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.error);
    } finally {
      setBusy(null);
    }
  }

  async function handleUpload() {
    if (!profileId) {
      setError(t.noProfile);
      return;
    }
    if (!file) return;
    setBusy("cv");
    setError(null);
    setStatus(null);
    setAi(null);
    try {
      const result = await uploadCV(profileId, file);
      setCv(result);
      setSkills(result.skills);
      setStatus(t.cvUploaded);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.error);
    } finally {
      setBusy(null);
    }
  }

  async function handleSaveSkills() {
    if (!profileId) return;
    setBusy("skills");
    setError(null);
    setStatus(null);
    try {
      const result = await updateSkills(
        profileId,
        skills.map((skill) => ({
          skill_id: skill.skill_id,
          level: skill.level,
          evidence: skill.evidence,
          confirmed: skill.confirmed,
        })),
      );
      setSkills(result.skills);
      setStatus(t.skillsSaved);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.error);
    } finally {
      setBusy(null);
    }
  }

  async function handleAnalyze() {
    if (!profileId || !cv) return;
    if (!consent) {
      setError(t.consent);
      return;
    }
    setBusy("ai");
    setError(null);
    setStatus(null);
    try {
      const result = await analyzeCV(profileId, cv.raw_text, true);
      setAi(result);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.error);
    } finally {
      setBusy(null);
    }
  }

  function updateSkill(index: number, patch: Partial<CVSkill>) {
    setSkills((current) =>
      current.map((skill, position) => (position === index ? { ...skill, ...patch } : skill)),
    );
  }

  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-lg font-bold text-white">
            PC
          </div>
          <span className="text-xl font-semibold tracking-tight">PractiCV</span>
        </Link>
        <div className="flex items-center gap-3">
          <Link href="/" className="text-sm font-medium text-slate-600 hover:text-emerald-700">
            {t.home}
          </Link>
          <div className="flex items-center gap-1 rounded-full border border-slate-300 bg-white p-1 text-sm">
            <button
              type="button"
              onClick={() => setLocale("es")}
              className={`rounded-full px-3 py-1 ${
                locale === "es" ? "bg-emerald-600 text-white" : "text-slate-600"
              }`}
            >
              ES
            </button>
            <button
              type="button"
              onClick={() => setLocale("en")}
              className={`rounded-full px-3 py-1 ${
                locale === "en" ? "bg-emerald-600 text-white" : "text-slate-600"
              }`}
            >
              EN
            </button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <h1 className="text-4xl font-semibold tracking-tight">{t.title}</h1>
        <p className="mt-3 max-w-3xl text-lg text-slate-600">{t.subtitle}</p>

        {status && (
          <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            {status}
          </div>
        )}
        {error && (
          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}

        <section className="mt-10 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="text-sm font-medium text-slate-700">
              {t.fullName}
              <input
                data-testid="profile-name"
                value={form.full_name}
                onChange={(event) => updateForm("full_name", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-600"
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              {t.email}
              <input
                data-testid="profile-email"
                value={form.email}
                onChange={(event) => updateForm("email", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-600"
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              {t.career}
              <input
                data-testid="profile-career"
                value={form.career}
                onChange={(event) => updateForm("career", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-600"
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              {t.cycle}
              <input
                type="number"
                min={1}
                max={20}
                value={form.cycle}
                onChange={(event) => updateForm("cycle", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-600"
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              {t.location}
              <input
                value={form.location}
                onChange={(event) => updateForm("location", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-600"
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              {t.targetRoles}
              <input
                value={form.target_roles}
                onChange={(event) => updateForm("target_roles", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-600"
              />
            </label>
          </div>
          <button
            type="button"
            data-testid="profile-save"
            onClick={handleSaveProfile}
            disabled={busy === "profile" || form.full_name.trim().length < 2}
            className="mt-6 rounded-full bg-emerald-700 px-6 py-3 text-sm font-semibold text-white disabled:opacity-50"
          >
            {busy === "profile" ? t.saving : t.save}
          </button>
        </section>

        <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">{t.upload}</h2>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <input
              data-testid="cv-file"
              type="file"
              accept=".pdf,.docx"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              className="text-sm"
            />
            <button
              type="button"
              data-testid="cv-upload"
              onClick={handleUpload}
              disabled={!file || busy === "cv" || !profileId}
              className="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
            >
              {busy === "cv" ? t.uploading : t.upload}
            </button>
          </div>

          {cv && (
            <div className="mt-6 space-y-4">
              {cv.warnings.length > 0 && (
                <ul className="list-disc space-y-1 rounded-xl bg-amber-50 p-4 pl-8 text-sm text-amber-900">
                  {cv.warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              )}
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                  {t.sections}
                </h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {Object.keys(cv.sections).map((section) => (
                    <span
                      key={section}
                      className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700"
                    >
                      {section}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </section>

        {skills.length > 0 && (
          <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-xl font-semibold">{t.skills}</h2>
              <button
                type="button"
                data-testid="skills-save"
                onClick={handleSaveSkills}
                disabled={busy === "skills"}
                className="rounded-full bg-emerald-700 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                {t.saveSkills}
              </button>
            </div>
            <div className="mt-4 divide-y divide-slate-100">
              {skills.map((skill, index) => (
                <div key={skill.skill_id} className="flex flex-wrap items-center gap-3 py-3">
                  <div className="min-w-48 flex-1">
                    <p className="font-medium">{skill.canonical_name}</p>
                    {skill.evidence && (
                      <p className="text-xs text-slate-500">{skill.evidence}</p>
                    )}
                  </div>
                  <label className="text-xs text-slate-500">
                    {t.level}
                    <select
                      data-testid={`skill-level-${index}`}
                      value={skill.level}
                      onChange={(event) =>
                        updateSkill(index, { level: Number(event.target.value) })
                      }
                      className="ml-2 rounded-lg border border-slate-300 px-2 py-1 text-sm"
                    >
                      <option value={0}>0</option>
                      <option value={1}>1</option>
                      <option value={2}>2</option>
                      <option value={3}>3</option>
                    </select>
                  </label>
                  <label className="flex items-center gap-2 text-xs text-slate-600">
                    <input
                      type="checkbox"
                      checked={skill.confirmed}
                      onChange={(event) =>
                        updateSkill(index, { confirmed: event.target.checked })
                      }
                    />
                    {t.confirmed}
                  </label>
                </div>
              ))}
            </div>
          </section>
        )}

        {cv && cv.warnings.length > 0 && (
          <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">{t.analyze}</h2>
            <label className="mt-4 flex items-start gap-2 text-sm text-slate-600">
              <input
                data-testid="ai-consent"
                type="checkbox"
                checked={consent}
                onChange={(event) => setConsent(event.target.checked)}
                className="mt-1"
              />
              {t.consent}
            </label>
            <button
              type="button"
              data-testid="ai-analyze"
              onClick={handleAnalyze}
              disabled={!consent || busy === "ai"}
              className="mt-4 rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
            >
              {t.analyze}
            </button>

            {ai && (
              <div className="mt-6 space-y-4" data-testid="ai-result">
                <div>
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                    {t.redacted}
                  </h3>
                  <pre className="mt-2 max-h-48 overflow-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-100">
                    {ai.redacted_text}
                  </pre>
                </div>
                <div>
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                    {t.aiResult}
                  </h3>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
                    {ai.suggestions.map((suggestion) => (
                      <li key={suggestion}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </section>
        )}
      </section>
    </main>
  );
}
