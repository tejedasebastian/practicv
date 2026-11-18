"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import {
  createApplication,
  createMatch,
  getOffer,
  overrideMatch,
  type Match,
  type Offer,
} from "@/lib/api";
import { dictionaries } from "@/lib/i18n";
import { useLocale } from "@/lib/useLocale";

const decisionKeys = {
  apply: "apply",
  apply_with_gaps: "applyWithGaps",
  improve_cv: "improveCv",
} as const;

export default function OfferDetailPage() {
  const params = useParams<{ id: string }>();
  const offerId = params.id;
  const [locale, setLocale] = useLocale();
  const t = dictionaries[locale].match;
  const nav = dictionaries[locale].nav;
  const [offer, setOffer] = useState<Offer | null>(null);
  const [profileId, setProfileId] = useState<string | null>(null);
  const [match, setMatch] = useState<Match | null>(null);
  const [decision, setDecision] = useState<Match["decision"]>("apply");
  const [reason, setReason] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    if (!offerId) return;
    getOffer(offerId).then(setOffer).catch((cause) => {
      setError(cause instanceof Error ? cause.message : "Offer not found");
    });
    setProfileId(window.localStorage.getItem("practicv.profileId"));
  }, [offerId]);

  async function handleMatch() {
    if (!profileId) {
      setError(t.profileMissing);
      return;
    }
    setBusy("match");
    setError(null);
    setStatus(null);
    try {
      const result = await createMatch(profileId, offerId);
      setMatch(result);
      setDecision(result.decision);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.profileMissing);
    } finally {
      setBusy(null);
    }
  }

  async function handleOverride() {
    if (!match) return;
    setBusy("override");
    setError(null);
    setStatus(null);
    try {
      const result = await overrideMatch(match.id, decision, reason || null);
      setMatch(result);
      setStatus(t.overrideSaved);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.profileMissing);
    } finally {
      setBusy(null);
    }
  }

  async function handleApplication() {
    if (!profileId) {
      setError(t.profileMissing);
      return;
    }
    setBusy("application");
    setError(null);
    setStatus(null);
    try {
      const result = await createApplication({
        profile_id: profileId,
        offer_id: offerId,
        status: "saved",
      });
      setStatus(result.duplicate ? t.applicationDuplicate : t.applicationCreated);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t.profileMissing);
    } finally {
      setBusy(null);
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
        <div className="flex items-center gap-3">
          <Link href="/ofertas" className="text-sm font-medium text-slate-600 hover:text-emerald-700">
            {t.back}
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
        {offer ? (
          <>
            <p className="text-sm font-medium uppercase tracking-widest text-emerald-700">
              {offer.source_type}
            </p>
            <h1 data-testid="offer-detail-title" className="mt-2 text-4xl font-semibold tracking-tight">
              {offer.title}
            </h1>
            <p className="mt-2 text-lg text-slate-600">
              {offer.company} · {offer.location ?? "—"} · {offer.modality ?? "—"}
            </p>
            {offer.salary_text && <p className="mt-1 text-slate-700">{offer.salary_text}</p>}
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                data-testid="match-calculate"
                onClick={handleMatch}
                disabled={busy === "match"}
                className="rounded-full bg-emerald-700 px-6 py-3 text-sm font-semibold text-white disabled:opacity-50"
              >
                {busy === "match" ? t.calculating : t.calculate}
              </button>
              <button
                type="button"
                data-testid="create-application"
                onClick={handleApplication}
                disabled={busy === "application"}
                className="rounded-full border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 disabled:opacity-50"
              >
                {t.application}
              </button>
            </div>

            {status && (
              <div data-testid="match-status" className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                {status}
              </div>
            )}
            {error && (
              <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                {error}
              </div>
            )}

            {match && (
              <div className="mt-8 space-y-6">
                <div className="grid gap-4 md:grid-cols-3">
                  <div data-testid="match-score" className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
                    <p className="text-sm font-medium uppercase tracking-wide text-emerald-800">{t.score}</p>
                    <p className="mt-2 text-4xl font-semibold text-emerald-900">{match.overall_score}%</p>
                    <p className="mt-1 text-xs text-emerald-800">
                      {t.confidence}: {match.confidence}%
                    </p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-white p-5">
                    <p className="text-sm font-medium uppercase tracking-wide text-slate-500">{t.mustHave}</p>
                    <p className="mt-2 text-4xl font-semibold">{match.must_have_score}%</p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-white p-5">
                    <p className="text-sm font-medium uppercase tracking-wide text-slate-500">{t.decision}</p>
                    <p data-testid="match-decision" className="mt-2 text-2xl font-semibold">
                      {t[decisionKeys[match.decision]]}
                    </p>
                    {match.overridden && (
                      <p className="mt-1 text-xs text-amber-700">Override: {match.override_reason}</p>
                    )}
                  </div>
                </div>

                <section className="rounded-2xl border border-slate-200 bg-white p-6">
                  <h2 className="text-xl font-semibold">{t.gaps}</h2>
                  {match.gaps_json.length === 0 ? (
                    <p className="mt-3 text-sm text-emerald-700">{t.noGaps}</p>
                  ) : (
                    <ul className="mt-3 space-y-3">
                      {match.gaps_json.map((gap, index) => (
                        <li key={`${gap.skill}-${index}`} data-testid={`match-gap-${index}`} className="rounded-xl bg-amber-50 p-4 text-sm text-amber-900">
                          <p className="font-semibold">{gap.skill}</p>
                          <p>
                            {gap.requirement_type} · requerido {gap.required_level} · tienes {gap.user_level}
                          </p>
                          <p className="mt-1">{gap.suggestion}</p>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>

                <section className="rounded-2xl border border-slate-200 bg-white p-6">
                  <h2 className="text-xl font-semibold">{t.explanation}</h2>
                  <div className="mt-3 divide-y divide-slate-100">
                    {match.explanation_json.map((item) => (
                      <div key={item.skill} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                        <span className="font-medium">{item.skill}</span>
                        <span className={item.status === "met" ? "text-emerald-700" : "text-amber-700"}>
                          {item.status} · {item.user_level}/{item.required_level} · {item.requirement_type}
                        </span>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="rounded-2xl border border-slate-200 bg-white p-6">
                  <h2 className="text-xl font-semibold">{t.override}</h2>
                  <div className="mt-3 flex flex-wrap items-end gap-3">
                    <label className="text-sm text-slate-600">
                      {t.decision}
                      <select
                        data-testid="match-override-decision"
                        value={decision}
                        onChange={(event) => setDecision(event.target.value as Match["decision"])}
                        className="ml-2 rounded-lg border border-slate-300 px-3 py-2 text-sm"
                      >
                        <option value="apply">{t.apply}</option>
                        <option value="apply_with_gaps">{t.applyWithGaps}</option>
                        <option value="improve_cv">{t.improveCv}</option>
                      </select>
                    </label>
                    <label className="text-sm text-slate-600">
                      {t.reason}
                      <input
                        value={reason}
                        onChange={(event) => setReason(event.target.value)}
                        className="ml-2 rounded-lg border border-slate-300 px-3 py-2 text-sm"
                      />
                    </label>
                    <button
                      type="button"
                      data-testid="match-override-save"
                      onClick={handleOverride}
                      disabled={busy === "override"}
                      className="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
                    >
                      {t.saveOverride}
                    </button>
                  </div>
                </section>
              </div>
            )}
          </>
        ) : (
          <p className="text-slate-500">{error ?? "Cargando oferta..."}</p>
        )}
      </section>
    </main>
  );
}
