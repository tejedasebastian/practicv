import en from "@/messages/en.json";
import es from "@/messages/es.json";

export type Locale = "es" | "en";

export const dictionaries = { es, en } as const;

export type Dictionary = (typeof dictionaries)[Locale];
