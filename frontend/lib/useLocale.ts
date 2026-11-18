"use client";

import { useEffect, useState } from "react";

import type { Locale } from "@/lib/i18n";

export function useLocale(): [Locale, (locale: Locale) => void] {
  const [locale, setLocale] = useState<Locale>("es");

  useEffect(() => {
    const saved = window.localStorage.getItem("practicv.locale");
    if (saved === "es" || saved === "en") {
      setLocale(saved);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("practicv.locale", locale);
    document.documentElement.lang = locale;
  }, [locale]);

  return [locale, setLocale];
}
