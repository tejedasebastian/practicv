"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  createBookmarkletOffer,
  previewBookmarklet,
  type BookmarkletPreview,
} from "@/lib/api";
import { decodeBookmarkletPayload } from "@/lib/bookmarklet";
import { dictionaries } from "@/lib/i18n";
import { useLocale } from "@/lib/useLocale";

type CaptureForm = {
  title: string;
  company: string;
  url: string;
  location: string;
  modality: string;
  salary: string;
  description: string;
  requirements: string;
  deadline: string;
};

const emptyForm: CaptureForm = {
  title: "",
  company: "",
  url: "",
  location: "",
  modality: "",
  salary: "",
  description: "",
  requirements: "",
  deadline: "",
};

export default function CapturePage() {
  const [locale, setLocale] = useLocale();
  const t = dictionaries[locale].capture;
  const nav = dictionaries[locale].nav;
  const [form, setForm] = useState<CaptureForm>(emptyForm);
  const [preview, setPreview] = useState<BookmarkletPreview | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const raw = window.location.hash.replace(/^#/, "");
    if (!raw) {
      setError(t.missing);
      return;
    }
    const payload = decodeBookmarkletPayload(raw);
    if (!payload) {
      setError(t.missing);
      return;
    }
    let active = true;
    previewBookmarklet(payload)
      .then((data) => {
        if (!active) return;
        setPreview(data);
        setWarnings(data.warnings);
        setForm({
          title: data.title,
          company: data.company,
          url: data.source_url,
          location: data.location ?? "",
          modality: data.modality ?? "",
          salary:
            data.salary_text ??
            (data.salary_amount !== null ? String(data.salary_amount) : ""),
          description: data.description ?? "",
          requirements: data.requirements_text ?? "",
          deadline: data.deadline_at ? data.deadline_at.slice(0, 10) : "",
        });
      })
      .catch((cause) => {
        if (active) setError(cause instanceof Error ? cause.message : t.error);
      });
    return () => {
      active = false;
    };
  }, [t]);

  function update(field: keyof CaptureForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function save() {
    setBusy(true);
    setError(null);
    setStatus(null);
    try {
      const result = await createBookmarkletOffer({
        title: form.title.trim(),
        company: form.company.trim(),
        source_url: form.url.trim() || null,
        location: form.location.trim() || null,
        modality: form.modality.trim() || null,
        salary_text: form.salary.trim() || null,
        description: form.description.trim() || null,
        requirements_text: form.requirements.trim() || null,
        deadline_at: form.deadline ? `${form.deadline}T00:00:00Z` : null,
      });
      setStatus(result.duplicate ? t.duplicate : t.saved);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.error);
    } finally {
      setBusy(false);
    }
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
        <div className="flex items-center gap-4">
          <Link href="/ofertas" className="text-sm font-medium text-slate-600 hover:text-emerald-700">
            {nav.offers}
          </Link>
          <Link href="/postulaciones" className="text-sm font-medium text-slate-600 hover:text-emerald-700">
            {nav.applications}
          </Link>
          <div className="flex items-center gap-1 rounded-full border border-slate-300 bg-white p-1 text-sm">
            <button
              type="button"
              onClick={() => setLocale("es")}
              className={`rounded-full px-3 py-1 ${locale === "es" ? "bg-emerald-600 text-white" : "text-slate-600"}`}
            >
              ES
            </button>
            <button
              type="button"
              onClick={() => setLocale("en")}
              className={`rounded-full px-3 py-1 ${locale === "en" ? "bg-emerald-600 text-white" : "text-slate-600"}`}
            >
              EN
            </button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-3xl px-6 pb-20">
        <h1 className="text-4xl font-semibold tracking-tight">{t.title}</h1>
        <p className="mt-3 text-lg text-slate-600">{t.subtitle}</p>

        {error && (
          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}
        {status && (
          <div
            data-testid="capture-status"
            className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
          >
            {status}
          </div>
        )}
        {warnings.length > 0 && (
          <ul
            data-testid="capture-warnings"
            className="mt-6 list-disc space-y-1 rounded-xl bg-amber-50 p-4 pl-8 text-sm text-amber-900"
          >
            {warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        )}
        {preview && (
          <p className="mt-4 text-sm text-slate-500">
            {t.confidence}: {Math.round(preview.confidence * 100)}%
          </p>
        )}

        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="text-sm font-medium text-slate-700">
              {t.offerTitle}
              <input
                data-testid="capture-title"
                value={form.title}
                onChange={(event) => update("title", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              {t.company}
              <input
                data-testid="capture-company"
                value={form.company}
                onChange={(event) => update("company", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="text-sm font-medium text-slate-700 md:col-span-2">
              {t.url}
              <input
                value={form.url}
                onChange={(event) => update("url", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              {t.location}
              <input
                value={form.location}
                onChange={(event) => update("location", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              {t.modality}
              <input
                value={form.modality}
                onChange={(event) => update("modality", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              {t.salary}
              <input
                value={form.salary}
                onChange={(event) => update("salary", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              {t.deadline}
              <input
                type="date"
                value={form.deadline}
                onChange={(event) => update("deadline", event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="text-sm font-medium text-slate-700 md:col-span-2">
              {t.description}
              <textarea
                value={form.description}
                onChange={(event) => update("description", event.target.value)}
                rows={3}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="text-sm font-medium text-slate-700 md:col-span-2">
              {t.requirements}
              <textarea
                value={form.requirements}
                onChange={(event) => update("requirements", event.target.value)}
                rows={3}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
          </div>
          <button
            type="button"
            data-testid="capture-save"
            onClick={save}
            disabled={busy || form.title.trim().length < 2 || form.company.trim().length < 2}
            className="mt-6 rounded-full bg-emerald-700 px-6 py-3 text-sm font-semibold text-white disabled:opacity-50"
          >
            {busy ? t.saving : t.save}
          </button>
        </div>

        <Link href="/ofertas" className="mt-8 inline-block text-sm font-semibold text-emerald-700 underline">
          {t.back}
        </Link>
      </section>
    </main>
  );
}
