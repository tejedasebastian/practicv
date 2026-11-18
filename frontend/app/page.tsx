"use client";

import { useEffect, useState } from "react";

import { dictionaries, type Locale } from "@/lib/i18n";

export default function Home() {
  const [locale, setLocale] = useState<Locale>("es");
  const t = dictionaries[locale];

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-lg font-bold text-white">
            PC
          </div>
          <span className="text-xl font-semibold tracking-tight">PractiCV</span>
        </div>

        <div className="flex items-center gap-2 rounded-full border border-slate-300 bg-white p-1 text-sm shadow-sm">
          <span className="px-2 text-slate-500">{t.nav.language}</span>
          <button
            type="button"
            data-testid="lang-es"
            aria-pressed={locale === "es"}
            onClick={() => setLocale("es")}
            className={`rounded-full px-3 py-1 font-medium transition ${
              locale === "es" ? "bg-emerald-600 text-white" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            {t.nav.es}
          </button>
          <button
            type="button"
            data-testid="lang-en"
            aria-pressed={locale === "en"}
            onClick={() => setLocale("en")}
            className={`rounded-full px-3 py-1 font-medium transition ${
              locale === "en" ? "bg-emerald-600 text-white" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            {t.nav.en}
          </button>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-6 pb-20 pt-12">
        <p
          className="mb-4 text-sm font-medium uppercase tracking-[0.2em] text-emerald-700"
          data-testid="phase-label"
        >
          {t.hero.eyebrow}
        </p>
        <h1
          className="max-w-3xl text-5xl font-semibold tracking-tight md:text-7xl"
          data-testid="app-title"
        >
          {t.hero.title}
        </h1>
        <p className="mt-6 max-w-2xl text-2xl text-slate-700" data-testid="hero-subtitle">
          {t.hero.subtitle}
        </p>
        <p className="mt-4 max-w-2xl text-lg text-slate-600">{t.hero.description}</p>

        <div className="mt-10 flex flex-wrap gap-3">
          <a
            href="#roadmap"
            className="rounded-full bg-emerald-700 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-800"
          >
            {t.hero.primaryCta}
          </a>
          <a
            href="#spec"
            className="rounded-full border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
          >
            {t.hero.secondaryCta}
          </a>
        </div>
      </section>

      <section
        id="roadmap"
        className="mx-auto grid max-w-6xl gap-4 px-6 pb-20 md:grid-cols-3"
        aria-label="Roadmap"
      >
        {t.features.map((feature) => (
          <article
            key={feature.title}
            className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <h2 className="text-lg font-semibold">{feature.title}</h2>
            <p className="mt-2 text-slate-600">{feature.description}</p>
          </article>
        ))}
      </section>

      <section id="spec" className="mx-auto max-w-6xl px-6 pb-20">
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-6 text-sm text-emerald-900">
          <p className="font-semibold">PractiCV v0.1.0 · Fase 0</p>
          <p className="mt-2">
            Scaffold listo: FastAPI, Next.js, PostgreSQL, Docker, CI y E2E. El producto se construye en
            los siguientes checkpoints del roadmap.
          </p>
        </div>
      </section>

      <footer className="border-t border-slate-200 bg-white/60">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-8 text-sm text-slate-500 md:flex-row md:items-center md:justify-between">
          <span>{t.footer}</span>
          <span>PractiCV · v0.1.0</span>
        </div>
      </footer>
    </main>
  );
}
