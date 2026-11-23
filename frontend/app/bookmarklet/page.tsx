"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { buildBookmarklet } from "@/lib/bookmarklet";
import { dictionaries } from "@/lib/i18n";
import { useLocale } from "@/lib/useLocale";

export default function BookmarkletPage() {
  const [locale, setLocale] = useLocale();
  const t = dictionaries[locale].bookmarklet;
  const nav = dictionaries[locale].nav;
  const [href, setHref] = useState("");
  const [copied, setCopied] = useState(false);
  const linkRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    const code = buildBookmarklet(window.location.origin);
    setHref(code);
    linkRef.current?.setAttribute("href", code);
  }, []);

  async function copyCode() {
    if (!href) return;
    try {
      await navigator.clipboard.writeText(href);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
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

        <div className="mt-8 rounded-2xl border border-emerald-200 bg-emerald-50 p-6">
          <a
            ref={linkRef}
            data-testid="bookmarklet-link"
            href="#"
            draggable
            onClick={(event) => event.preventDefault()}
            className="inline-flex cursor-grab items-center gap-2 rounded-full bg-emerald-700 px-6 py-3 text-sm font-semibold text-white shadow-sm active:cursor-grabbing"
          >
            <span aria-hidden="true">+</span>
            {t.install}
          </a>
          <p className="mt-4 text-sm text-emerald-900">{t.note}</p>
          <button
            type="button"
            data-testid="bookmarklet-copy"
            onClick={copyCode}
            className="mt-4 rounded-full border border-emerald-300 bg-white px-4 py-2 text-sm font-medium text-emerald-800"
          >
            {copied ? t.copied : t.copy}
          </button>
        </div>

        <ol className="mt-8 space-y-3 text-slate-700">
          <li className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">1</span>
            {t.step1}
          </li>
          <li className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">2</span>
            {t.step2}
          </li>
          <li className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">3</span>
            {t.step3}
          </li>
        </ol>

        <Link href="/ofertas" className="mt-10 inline-block text-sm font-semibold text-emerald-700 underline">
          {t.back}
        </Link>
      </section>
    </main>
  );
}
