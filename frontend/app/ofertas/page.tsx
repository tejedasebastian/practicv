"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  captureOfferUrl,
  createOffer,
  getPractilizateStatus,
  getSourceStatus,
  importEmailAlerts,
  importMCP,
  importOffersCsv,
  importPractilizateCsv,
  listOffers,
  previewEmailAlerts,
  searchMCP,
  type EmailPreview,
  type MCPSearchResult,
  type Offer,
  type OfferImportResult,
  type PractilizateStatus,
  type SourceStatus,
} from "@/lib/api";
import { dictionaries } from "@/lib/i18n";
import { useLocale } from "@/lib/useLocale";

type Tab = "manual" | "csv" | "url" | "mcp" | "email" | "practilizate";

type ManualForm = {
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

const emptyManual: ManualForm = {
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

export default function OffersPage() {
  const [locale, setLocale] = useLocale();
  const t = dictionaries[locale].offers;
  const nav = dictionaries[locale].nav;
  const bookmarklet = dictionaries[locale].bookmarklet;
  const [tab, setTab] = useState<Tab>("manual");
  const [manual, setManual] = useState<ManualForm>(emptyManual);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<OfferImportResult | null>(null);
  const [capture, setCapture] = useState("");
  const [mcpQuery, setMcpQuery] = useState("");
  const [mcpCareer, setMcpCareer] = useState("");
  const [mcpDepartment, setMcpDepartment] = useState("");
  const [mcpResult, setMcpResult] = useState<MCPSearchResult | null>(null);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [sourceStatus, setSourceStatus] = useState<SourceStatus | null>(null);
  const [emailFile, setEmailFile] = useState<File | null>(null);
  const [emailPreview, setEmailPreview] = useState<EmailPreview | null>(null);
  const [emailSelected, setEmailSelected] = useState<Record<string, boolean>>({});
  const [practilizateStatus, setPractilizateStatus] = useState<PractilizateStatus | null>(null);
  const [practilizateFile, setPractilizateFile] = useState<File | null>(null);

  const refreshOffers = useCallback(async () => {
    try {
      setOffers(await listOffers());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.noOffers);
    }
  }, [t.noOffers]);

  useEffect(() => {
    refreshOffers();
    getSourceStatus()
      .then(setSourceStatus)
      .catch(() => setSourceStatus({ mcp: "unavailable", detail: null, filters: null }));
    getPractilizateStatus()
      .then(setPractilizateStatus)
      .catch(() => setPractilizateStatus({ enabled: false, detail: "" }));
  }, [refreshOffers]);

  function updateManual(field: keyof ManualForm, value: string) {
    setManual((current) => ({ ...current, [field]: value }));
  }

  async function handleManual() {
    setBusy("manual");
    setError(null);
    setStatus(null);
    try {
      const salaryAmount = manual.salary
        ? Number(manual.salary.replace(/[^0-9.]/g, "")) || null
        : null;
      const result = await createOffer({
        title: manual.title,
        company: manual.company,
        source_url: manual.url || null,
        location: manual.location || null,
        modality: manual.modality || null,
        salary_text: manual.salary || null,
        salary_amount: salaryAmount,
        description: manual.description || null,
        requirements_text: manual.requirements || null,
        deadline_at: manual.deadline ? new Date(manual.deadline).toISOString() : null,
      });
      setOffers((current) => [result.offer, ...current]);
      setStatus(result.duplicate ? t.duplicate : t.created);
      setManual(emptyManual);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.noOffers);
    } finally {
      setBusy(null);
    }
  }

  async function handleCsv() {
    if (!file) return;
    setBusy("csv");
    setError(null);
    setStatus(null);
    try {
      const result = await importOffersCsv(file);
      setImportResult(result);
      setStatus(t.created);
      await refreshOffers();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.noOffers);
    } finally {
      setBusy(null);
    }
  }

  async function handleEmailPreview() {
    if (!emailFile) return;
    setBusy("email-preview");
    setError(null);
    setStatus(null);
    try {
      const result = await previewEmailAlerts(emailFile);
      setEmailPreview(result);
      setEmailSelected(
        Object.fromEntries(result.candidates.map((candidate) => [candidate.url, true])),
      );
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.emailNoCandidates);
    } finally {
      setBusy(null);
    }
  }

  async function handleEmailImport() {
    const urls = Object.entries(emailSelected)
      .filter(([, checked]) => checked)
      .map(([url]) => url);
    if (urls.length === 0) return;
    setBusy("email-import");
    setError(null);
    setStatus(null);
    try {
      const result = await importEmailAlerts(urls);
      setImportResult(result);
      setStatus(t.created);
      await refreshOffers();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.noOffers);
    } finally {
      setBusy(null);
    }
  }

  async function handlePractilizate() {
    if (!practilizateFile) return;
    setBusy("practilizate");
    setError(null);
    setStatus(null);
    try {
      const result = await importPractilizateCsv(practilizateFile);
      setImportResult(result);
      setStatus(t.created);
      await refreshOffers();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.noOffers);
    } finally {
      setBusy(null);
    }
  }

  async function handleCapture() {
    setBusy("url");
    setError(null);
    setStatus(null);
    try {
      const result = await captureOfferUrl(capture);
      setOffers((current) => [result.offer, ...current]);
      setStatus(result.duplicate ? t.duplicate : t.created);
      setCapture("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.noOffers);
    } finally {
      setBusy(null);
    }
  }

  async function handleMcpSearch() {
    setBusy("mcp");
    setError(null);
    setStatus(null);
    try {
      const result = await searchMCP({
        q: mcpQuery,
        career: mcpCareer || undefined,
        department: mcpDepartment || undefined,
        limit: 20,
      });
      setMcpResult(result);
      setSelected(Object.fromEntries(result.results.map((item) => [item.url, true])));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.noOffers);
    } finally {
      setBusy(null);
    }
  }

  async function handleMcpImport() {
    const urls = Object.entries(selected)
      .filter(([, checked]) => checked)
      .map(([url]) => url);
    if (urls.length === 0) return;
    setBusy("mcp-import");
    setError(null);
    setStatus(null);
    try {
      const result = await importMCP(urls);
      setImportResult(result);
      setStatus(t.created);
      await refreshOffers();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.noOffers);
    } finally {
      setBusy(null);
    }
  }

  const tabClass = (value: Tab) =>
    `rounded-full px-4 py-2 text-sm font-medium transition ${
      tab === value ? "bg-emerald-700 text-white" : "bg-white text-slate-600 hover:bg-slate-100"
    }`;

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
          <Link href="/" className="text-sm font-medium text-slate-600 hover:text-emerald-700">
            {t.home}
          </Link>
          <Link
            href="/perfil"
            className="text-sm font-medium text-slate-600 hover:text-emerald-700"
          >
            {nav.profile}
          </Link>
          <Link
            href="/postulaciones"
            className="text-sm font-medium text-slate-600 hover:text-emerald-700"
          >
            {nav.applications}
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
        <h1 data-testid="offers-title" className="text-4xl font-semibold tracking-tight">
          {t.title}
        </h1>
        <p className="mt-3 max-w-3xl text-lg text-slate-600">{t.subtitle}</p>

        <div className="mt-4 flex flex-wrap items-center gap-2 text-sm">
          <span
            className={`rounded-full px-3 py-1 ${
              sourceStatus?.mcp === "available"
                ? "bg-emerald-100 text-emerald-800"
                : "bg-amber-100 text-amber-800"
            }`}
          >
            {sourceStatus?.mcp === "available" ? t.mcpAvailable : t.mcpUnavailable}
          </span>
        </div>

        {status && (
          <div
            data-testid="offers-status"
            className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
          >
            {status}
          </div>
        )}
        {error && (
          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}

        <div className="mt-8 flex flex-wrap gap-2">
          <button type="button" data-testid="offers-tab-manual" onClick={() => setTab("manual")} className={tabClass("manual")}>
            {t.manual}
          </button>
          <button type="button" data-testid="offers-tab-csv" onClick={() => setTab("csv")} className={tabClass("csv")}>
            {t.csv}
          </button>
          <button type="button" data-testid="offers-tab-email" onClick={() => setTab("email")} className={tabClass("email")}>
            {t.email}
          </button>
          <button type="button" data-testid="offers-tab-practilizate" onClick={() => setTab("practilizate")} className={tabClass("practilizate")}>
            {t.practilizate}
          </button>
          <button type="button" data-testid="offers-tab-url" onClick={() => setTab("url")} className={tabClass("url")}>
            {t.url}
          </button>
          <button type="button" data-testid="offers-tab-mcp" onClick={() => setTab("mcp")} className={tabClass("mcp")}>
            {t.mcp}
          </button>
          <Link
            href="/bookmarklet"
            data-testid="bookmarklet-install-link"
            className="ml-auto rounded-full border border-emerald-300 bg-white px-4 py-2 text-sm font-medium text-emerald-800 hover:bg-emerald-50"
          >
            {bookmarklet.install}
          </Link>
        </div>

        {tab === "manual" && (
          <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="text-sm font-medium text-slate-700">
                {t.offerTitle}
                <input data-testid="offer-title" value={manual.title} onChange={(event) => updateManual("title", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700">
                {t.company}
                <input data-testid="offer-company" value={manual.company} onChange={(event) => updateManual("company", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700">
                {t.urlLabel}
                <input data-testid="offer-url" value={manual.url} onChange={(event) => updateManual("url", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700">
                {t.location}
                <input value={manual.location} onChange={(event) => updateManual("location", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700">
                {t.modality}
                <input value={manual.modality} onChange={(event) => updateManual("modality", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700">
                {t.salary}
                <input value={manual.salary} onChange={(event) => updateManual("salary", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700 md:col-span-2">
                {t.description}
                <textarea value={manual.description} onChange={(event) => updateManual("description", event.target.value)} rows={3} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700 md:col-span-2">
                {t.requirements}
                <textarea value={manual.requirements} onChange={(event) => updateManual("requirements", event.target.value)} rows={3} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700">
                {t.deadline}
                <input type="date" value={manual.deadline} onChange={(event) => updateManual("deadline", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
            </div>
            <button type="button" data-testid="offer-save" onClick={handleManual} disabled={busy === "manual" || manual.title.trim().length < 2 || manual.company.trim().length < 2} className="mt-6 rounded-full bg-emerald-700 px-6 py-3 text-sm font-semibold text-white disabled:opacity-50">
              {busy === "manual" ? t.saving : t.save}
            </button>
          </section>
        )}

        {tab === "csv" && (
          <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">{t.csv}</h2>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <a
                href="/plantilla_ofertas.csv"
                download
                className="text-sm font-medium text-emerald-700 underline"
              >
                {t.template}
              </a>
              <input data-testid="offer-csv" type="file" accept=".csv,.xlsx" onChange={(event) => setFile(event.target.files?.[0] ?? null)} className="text-sm" />
              <button type="button" data-testid="offer-csv-import" onClick={handleCsv} disabled={!file || busy === "csv"} className="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50">
                {busy === "csv" ? t.importing : t.import}
              </button>
            </div>
            {importResult && <ImportSummary result={importResult} t={t} />}
          </section>
        )}

        {tab === "email" && (
          <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">{t.email}</h2>
            <p className="mt-2 text-sm text-slate-600">{t.emailHelp}</p>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <label className="text-sm font-medium text-slate-700">
                {t.emailFile}
                <input
                  data-testid="offer-email"
                  type="file"
                  accept=".eml,message/rfc822"
                  onChange={(event) => {
                    setEmailFile(event.target.files?.[0] ?? null);
                    setEmailPreview(null);
                  }}
                  className="ml-2 text-sm"
                />
              </label>
              <button
                type="button"
                data-testid="email-preview"
                onClick={handleEmailPreview}
                disabled={!emailFile || busy === "email-preview"}
                className="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                {busy === "email-preview" ? t.emailPreviewing : t.emailPreview}
              </button>
            </div>

            {emailPreview && (
              <div className="mt-6">
                <p className="text-sm font-medium text-slate-700">
                  {t.emailSubject}: {emailPreview.subject || "—"}
                </p>
                {emailPreview.warnings.length > 0 && (
                  <ul className="mt-3 list-disc space-y-1 rounded-xl bg-amber-50 p-4 pl-8 text-sm text-amber-900">
                    {emailPreview.warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                )}
                <div className="mt-4 flex items-center justify-between gap-3">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                    {t.emailCandidates} ({emailPreview.candidates.length})
                  </h3>
                  <button
                    type="button"
                    data-testid="email-import"
                    onClick={handleEmailImport}
                    disabled={busy === "email-import" || emailPreview.candidates.length === 0}
                    className="rounded-full bg-emerald-700 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
                  >
                    {t.emailImport}
                  </button>
                </div>
                {emailPreview.candidates.length === 0 ? (
                  <p className="mt-3 text-sm text-slate-500">{t.emailNoCandidates}</p>
                ) : (
                  <div className="mt-3 divide-y divide-slate-100">
                    {emailPreview.candidates.map((candidate, index) => (
                      <label
                        key={candidate.url}
                        data-testid={`email-candidate-${index}`}
                        className="flex items-start gap-3 py-3 text-sm"
                      >
                        <input
                          type="checkbox"
                          checked={emailSelected[candidate.url] ?? false}
                          onChange={(event) =>
                            setEmailSelected((current) => ({
                              ...current,
                              [candidate.url]: event.target.checked,
                            }))
                          }
                          className="mt-1"
                        />
                        <span>
                          <span className="font-medium">{candidate.title}</span>
                          <span className="block break-all text-xs text-slate-500">
                            {candidate.url}
                          </span>
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            )}
            {importResult && <ImportSummary result={importResult} t={t} />}
          </section>
        )}

        {tab === "practilizate" && (
          <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">{t.practilizate}</h2>
            <p className="mt-2 text-sm text-slate-600">{t.practilizateHelp}</p>
            <div
              data-testid="practilizate-status"
              className={`mt-4 rounded-xl border px-4 py-3 text-sm ${
                practilizateStatus?.enabled
                  ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                  : "border-amber-200 bg-amber-50 text-amber-800"
              }`}
            >
              {practilizateStatus?.enabled ? t.practilizateEnabled : t.practilizateDisabled}
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <label className="text-sm font-medium text-slate-700">
                {t.practilizateFile}
                <input
                  data-testid="practilizate-file"
                  type="file"
                  accept=".csv"
                  disabled={!practilizateStatus?.enabled}
                  onChange={(event) => setPractilizateFile(event.target.files?.[0] ?? null)}
                  className="ml-2 text-sm"
                />
              </label>
              <button
                type="button"
                data-testid="practilizate-import"
                onClick={handlePractilizate}
                disabled={
                  !practilizateStatus?.enabled ||
                  !practilizateFile ||
                  busy === "practilizate"
                }
                className="rounded-full bg-emerald-700 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                {t.practilizateImport}
              </button>
            </div>
            {importResult && <ImportSummary result={importResult} t={t} />}
          </section>
        )}

        {tab === "url" && (
          <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">{t.capture}</h2>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <input data-testid="offer-capture-url" value={capture} onChange={(event) => setCapture(event.target.value)} placeholder="https://..." className="min-w-80 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              <button type="button" data-testid="offer-capture" onClick={handleCapture} disabled={capture.length < 5 || busy === "url"} className="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50">
                {busy === "url" ? t.capturing : t.capture}
              </button>
            </div>
          </section>
        )}

        {tab === "mcp" && (
          <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">{t.search}</h2>
            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <label className="text-sm font-medium text-slate-700">
                {t.query}
                <input data-testid="mcp-query" value={mcpQuery} onChange={(event) => setMcpQuery(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700">
                {t.career}
                <input data-testid="mcp-career" value={mcpCareer} onChange={(event) => setMcpCareer(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700">
                {t.department}
                <input data-testid="mcp-department" value={mcpDepartment} onChange={(event) => setMcpDepartment(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
            </div>
            <button type="button" data-testid="mcp-search" onClick={handleMcpSearch} disabled={busy === "mcp"} className="mt-4 rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50">
              {busy === "mcp" ? t.searching : t.search}
            </button>

            {mcpResult && (
              <div className="mt-6">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                    {t.results} ({mcpResult.total})
                  </h3>
                  <button type="button" data-testid="mcp-import" onClick={handleMcpImport} disabled={busy === "mcp-import"} className="rounded-full bg-emerald-700 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50">
                    {t.importSelected}
                  </button>
                </div>
                <div className="mt-3 divide-y divide-slate-100">
                  {mcpResult.results.map((item, index) => (
                    <label key={item.url} data-testid={`mcp-result-${index}`} className="flex items-start gap-3 py-3 text-sm">
                      <input type="checkbox" checked={selected[item.url] ?? false} onChange={(event) => setSelected((current) => ({ ...current, [item.url]: event.target.checked }))} className="mt-1" />
                      <span>
                        <span className="font-medium">{item.titulo}</span>
                        <span className="text-slate-500"> · {item.empresa}</span>
                        <span className="block text-xs text-slate-500">{item.ubicacion} · {item.modalidad} · {item.subvencion}</span>
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}
            {importResult && <ImportSummary result={importResult} t={t} />}
          </section>
        )}

        <section className="mt-10">
          <h2 className="text-2xl font-semibold">{t.list}</h2>
          {offers.length === 0 ? (
            <p className="mt-3 text-slate-500">{t.noOffers}</p>
          ) : (
            <div data-testid="offers-list" className="mt-4 grid gap-3">
              {offers.map((offer) => (
                <article key={offer.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <h3 className="font-semibold">{offer.title}</h3>
                      <p className="text-sm text-slate-500">{offer.company} · {offer.location ?? "—"}</p>
                    </div>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                      {t.source}: {offer.source_type}
                    </span>
                    <Link
                      href={`/ofertas/${offer.id}`}
                      className="text-sm font-semibold text-emerald-700 hover:text-emerald-900"
                    >
                      Match →
                    </Link>
                  </div>
                  {offer.salary_text && <p className="mt-2 text-sm text-slate-600">{offer.salary_text}</p>}
                </article>
              ))}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

function ImportSummary({
  result,
  t,
}: {
  result: OfferImportResult;
  t: (typeof dictionaries)["es"]["offers"];
}) {
  return (
    <div className="mt-6 space-y-3" data-testid="import-summary">
      <div className="flex flex-wrap gap-3 text-sm">
        <span className="rounded-full bg-emerald-50 px-3 py-1 text-emerald-800">
          {t.createdCount}: {result.created}
        </span>
        <span className="rounded-full bg-amber-50 px-3 py-1 text-amber-800">
          {t.duplicatesCount}: {result.duplicates}
        </span>
        <span className="rounded-full bg-red-50 px-3 py-1 text-red-800">
          {t.errorsCount}: {result.errors.length}
        </span>
      </div>
      {result.warnings.length > 0 && (
        <ul className="list-disc space-y-1 rounded-xl bg-amber-50 p-4 pl-8 text-sm text-amber-900">
          {result.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      )}
      {result.preview.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            {t.preview}
          </h3>
          <ul className="mt-2 space-y-1 text-sm text-slate-700">
            {result.preview.map((item) => (
              <li key={`${item.title}-${item.company}`}>
                {item.title} · {item.company} · {item.salary_amount ?? "sin sueldo"}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
