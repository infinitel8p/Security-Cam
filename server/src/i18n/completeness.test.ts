import { describe, it as test, expect } from "vitest";
import en from "./en";
import de from "./de";
import fr from "./fr";
import es from "./es";
import italiano from "./it";

/** Recursively collect all dot-path keys from an object */
function collectKeys(obj: Record<string, unknown>, prefix = ""): string[] {
  const keys: string[] = [];
  for (const [k, v] of Object.entries(obj)) {
    const path = prefix ? `${prefix}.${k}` : k;
    if (typeof v === "object" && v !== null && !Array.isArray(v)) {
      keys.push(...collectKeys(v as Record<string, unknown>, path));
    } else {
      keys.push(path);
    }
  }
  return keys.sort();
}

const enKeys = collectKeys(en);

const languages: [string, Record<string, unknown>][] = [
  ["de", de as unknown as Record<string, unknown>],
  ["fr", fr as unknown as Record<string, unknown>],
  ["es", es as unknown as Record<string, unknown>],
  ["it", italiano as unknown as Record<string, unknown>],
];

describe("i18n completeness", () => {
  for (const [lang, translations] of languages) {
    test(`${lang} has all keys from en`, () => {
      const langKeys = collectKeys(translations);
      const missing = enKeys.filter((k) => !langKeys.includes(k));
      expect(missing, `Missing keys in ${lang}: ${missing.join(", ")}`).toEqual([]);
    });
  }
});
