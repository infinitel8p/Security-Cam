import en from "./en";
import de from "./de";
import fr from "./fr";
import es from "./es";
import it from "./it";

export type Locale = "en" | "de" | "fr" | "es" | "it";

const locales: Locale[] = ["en", "de", "fr", "es", "it"];

type DeepStringRecord = { [key: string]: string | DeepStringRecord };

const translations: Record<Locale, DeepStringRecord> = { en, de, fr, es, it };

let currentLocale: Locale = "en";
let listeners: Array<() => void> = [];

function detectLocale(): Locale {
  const saved = typeof localStorage !== "undefined" ? localStorage.getItem("locale") : null;
  if (saved && locales.includes(saved as Locale)) return saved as Locale;
  const browser = typeof navigator !== "undefined" ? navigator.language : "en";
  const prefix = browser.split("-")[0] as Locale;
  return locales.includes(prefix) ? prefix : "en";
}

export function initLocale(): void {
  currentLocale = detectLocale();
}

export function getLocale(): Locale {
  return currentLocale;
}

export function setLocale(locale: Locale): void {
  currentLocale = locale;
  if (typeof localStorage !== "undefined") {
    localStorage.setItem("locale", locale);
  }
  listeners.forEach((fn) => fn());
}

export function subscribe(fn: () => void): () => void {
  listeners.push(fn);
  return () => {
    listeners = listeners.filter((l) => l !== fn);
  };
}

/** Get a nested translation value by dot-path key. */
export function t(key: string, params?: Record<string, string | number>): string {
  const keys = key.split(".");
  let value: any = translations[currentLocale];
  for (const k of keys) {
    value = value?.[k];
    if (value === undefined) {
      // Fallback to English
      value = translations.en;
      for (const fk of keys) {
        value = value?.[fk];
        if (value === undefined) return key;
      }
      break;
    }
  }
  if (typeof value !== "string") return key;
  if (params) {
    return value.replace(/\{(\w+)\}/g, (_, k) => String(params[k] ?? `{${k}}`));
  }
  return value;
}
