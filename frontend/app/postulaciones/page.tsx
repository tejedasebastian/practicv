"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  addReminder,
  exportUrl,
  listApplications,
  updateApplication,
  type Application,
  type ApplicationWithOffer,
} from "@/lib/api";
import { dictionaries } from "@/lib/i18n";
import { useLocale } from "@/lib/useLocale";

const columns: Array<Application["status"]> = [
  "saved",
  "applied",
  "interview",
  "rejected",
  "offer",
];

export default function ApplicationsPage() {
  const [locale, setLocale] = useLocale();
  const t = dictionaries[locale].applications;
  const nav = dictionaries[locale].nav;
  const [profileId, setProfileId] = useState<string | null>(null);
  const [applications, setApplications] = useState<ApplicationWithOffer[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [reminderDates, setReminderDates] = useState<Record<string, string>>({});
  const [reminderMessages, setReminderMessages] = useState<Record<string, string>>({});
  const [filterStatus, setFilterStatus] = useState<"all" | Application["status"]>("all");
  const [filterDeadline, setFilterDeadline] = useState<"all" | "next7">("all");
  const [filterMatch, setFilterMatch] = useState<"all" | "with" | "high">("all");
  const [search, setSearch] = useState("");

  const refresh = useCallback(async (id: string) => {
    try {
      setApplications(await listApplications(id));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.profileMissing);
    }
  }, [t.profileMissing]);

  useEffect(() => {
    const saved = window.localStorage.getItem("practicv.profileId");
    setProfileId(saved);
    if (saved) {
      refresh(saved);
    }
  }, [refresh]);

  async function handleStatus(applicationId: string, next: Application["status"]) {
    setBusy(applicationId);
    setError(null);
    setStatus(null);
    try {
      const updated = await updateApplication(applicationId, { status: next });
      setApplications((current) =>
        current.map((item) =>
          item.application.id === applicationId
            ? { ...item, application: updated }
            : item,
        ),
      );
      setStatus(`${t[next]}`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.profileMissing);
    } finally {
      setBusy(null);
    }
  }

  async function handleReminder(applicationId: string) {
    const date = reminderDates[applicationId];
    if (!date) return;
    setBusy(`reminder-${applicationId}`);
    setError(null);
    setStatus(null);
    try {
      await addReminder(applicationId, {
        due_at: new Date(`${date}T09:00:00`).toISOString(),
        channel: "in_app",
        message: reminderMessages[applicationId] || null,
      });
      setStatus(t.reminderAdded);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.profileMissing);
    } finally {
      setBusy(null);
    }
  }

  const filteredApplications = applications.filter((item) => {
    if (filterStatus !== "all" && item.application.status !== filterStatus) return false;
    if (filterMatch === "with" && !item.match) return false;
    if (filterMatch === "high" && (!item.match || item.match.overall_score < 80)) {
      return false;
    }
    if (filterDeadline === "next7") {
      if (!item.offer.deadline_at) return false;
      const remaining = new Date(item.offer.deadline_at).getTime() - Date.now();
      if (remaining < 0 || remaining > 7 * 24 * 60 * 60 * 1000) return false;
    }
    if (search) {
      const haystack = `${item.offer.title} ${item.offer.company}`.toLowerCase();
      if (!haystack.includes(search.toLowerCase())) return false;
    }
    return true;
  });

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
          <Link href="/ofertas" className="text-sm font-medium text-slate-600 hover:text-emerald-700">
            {nav.offers}
          </Link>
          <Link href="/perfil" className="text-sm font-medium text-slate-600 hover:text-emerald-700">
            {nav.profile}
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

      <section className="mx-auto max-w-7xl px-6 pb-20">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 data-testid="applications-title" className="text-4xl font-semibold tracking-tight">
              {t.title}
            </h1>
            <p className="mt-2 text-lg text-slate-600">{t.subtitle}</p>
          </div>
          {profileId && (
            <div className="flex flex-wrap gap-2 text-sm">
              <a data-testid="export-xlsx" href={exportUrl("applications.xlsx", profileId)} className="rounded-full border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700">
                {t.excel}
              </a>
              <a data-testid="export-csv" href={exportUrl("applications.csv", profileId)} className="rounded-full border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700">
                {t.csv}
              </a>
              <a data-testid="export-ics" href={exportUrl("calendar.ics", profileId)} className="rounded-full border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700">
                {t.ics}
              </a>
            </div>
          )}
        </div>

        {!profileId && (
          <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {t.profileMissing}
          </div>
        )}
        {status && (
          <div data-testid="applications-status" className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            {status}
          </div>
        )}
        {error && (
          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}

        {profileId && (
          <div className="mt-6 flex flex-wrap items-end gap-3 rounded-2xl border border-slate-200 bg-white p-4">
            <label className="text-sm text-slate-600">
              {t.statusLabel}
              <select
                data-testid="kanban-filter-status"
                value={filterStatus}
                onChange={(event) => setFilterStatus(event.target.value as typeof filterStatus)}
                className="ml-2 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                <option value="all">{t.all}</option>
                {columns.map((value) => (
                  <option key={value} value={value}>
                    {t[value]}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm text-slate-600">
              {t.deadlineLabel}
              <select
                data-testid="kanban-filter-deadline"
                value={filterDeadline}
                onChange={(event) => setFilterDeadline(event.target.value as typeof filterDeadline)}
                className="ml-2 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                <option value="all">{t.all}</option>
                <option value="next7">{t.next7}</option>
              </select>
            </label>
            <label className="text-sm text-slate-600">
              {t.matchLabel}
              <select
                data-testid="kanban-filter-match"
                value={filterMatch}
                onChange={(event) => setFilterMatch(event.target.value as typeof filterMatch)}
                className="ml-2 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                <option value="all">{t.all}</option>
                <option value="with">{t.withMatch}</option>
                <option value="high">{t.highMatch}</option>
              </select>
            </label>
            <label className="min-w-56 flex-1 text-sm text-slate-600">
              <input
                data-testid="kanban-search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder={t.searchPlaceholder}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
          </div>
        )}

        {profileId && applications.length === 0 && (
          <p className="mt-8 text-slate-500">{t.empty}</p>
        )}

        <div className="mt-8 grid gap-4 lg:grid-cols-5">
          {columns.map((column) => (
            <section
              key={column}
              data-testid={`kanban-column-${column}`}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                const applicationId = event.dataTransfer.getData("text/plain");
                if (applicationId) {
                  handleStatus(applicationId, column);
                }
              }}
              className="rounded-2xl border border-slate-200 bg-slate-50 p-3"
            >
              <h2 className="px-2 py-1 text-sm font-semibold uppercase tracking-wide text-slate-600">
                {t[column]}
              </h2>
              <div className="mt-2 space-y-3">
                {filteredApplications
                  .filter((item) => item.application.status === column)
                  .map((item, index) => (
                    <article
                      key={item.application.id}
                      data-testid={`application-card-${index}`}
                      draggable
                      onDragStart={(event) =>
                        event.dataTransfer.setData("text/plain", item.application.id)
                      }
                      className="cursor-grab rounded-xl border border-slate-200 bg-white p-3 shadow-sm active:cursor-grabbing"
                    >
                      <h3 className="text-sm font-semibold">{item.offer.title}</h3>
                      <p className="text-xs text-slate-500">{item.offer.company}</p>
                      {item.match && (
                        <p className="mt-1 text-xs font-medium text-emerald-700">
                          Match: {item.match.overall_score}% · {item.match.decision}
                        </p>
                      )}
                      <select
                        data-testid={`application-status-${index}`}
                        value={item.application.status}
                        onChange={(event) =>
                          handleStatus(
                            item.application.id,
                            event.target.value as Application["status"],
                          )
                        }
                        disabled={busy === item.application.id}
                        className="mt-2 w-full rounded-lg border border-slate-300 px-2 py-1 text-xs"
                      >
                        {columns.map((value) => (
                          <option key={value} value={value}>
                            {t[value]}
                          </option>
                        ))}
                      </select>
                      {item.application.next_action_note && (
                        <p className="mt-2 text-xs text-slate-600">
                          {t.nextAction}: {item.application.next_action_note}
                        </p>
                      )}
                      <div className="mt-2 space-y-1">
                        <input
                          data-testid={`application-reminder-date-${index}`}
                          type="date"
                          value={reminderDates[item.application.id] ?? ""}
                          onChange={(event) =>
                            setReminderDates((current) => ({
                              ...current,
                              [item.application.id]: event.target.value,
                            }))
                          }
                          className="w-full rounded-lg border border-slate-300 px-2 py-1 text-xs"
                        />
                        <input
                          value={reminderMessages[item.application.id] ?? ""}
                          onChange={(event) =>
                            setReminderMessages((current) => ({
                              ...current,
                              [item.application.id]: event.target.value,
                            }))
                          }
                          placeholder={t.reminderMessage}
                          className="w-full rounded-lg border border-slate-300 px-2 py-1 text-xs"
                        />
                        <button
                          type="button"
                          data-testid={`application-reminder-add-${index}`}
                          onClick={() => handleReminder(item.application.id)}
                          disabled={!reminderDates[item.application.id]}
                          className="w-full rounded-lg bg-slate-900 px-2 py-1 text-xs font-semibold text-white disabled:opacity-50"
                        >
                          {t.addReminder}
                        </button>
                      </div>
                    </article>
                  ))}
              </div>
            </section>
          ))}
        </div>
      </section>
    </main>
  );
}
