import type { Studio, Metro } from "./types";
import { STUDIOS } from "./data";
import { SITE } from "./site";
import { present } from "./format";

// ---- Modality predicates -------------------------------------------------

export function mods(s: Studio): string[] {
  return Array.isArray(s.modalities) ? s.modalities : [];
}

export function hasColdPlunge(s: Studio): boolean {
  return mods(s).includes("cold_plunge");
}

export function hasSauna(s: Studio): boolean {
  return mods(s).some((m) => m === "sauna_infrared" || m === "sauna_traditional" || m === "sauna");
}

export function hasInfrared(s: Studio): boolean {
  return mods(s).includes("sauna_infrared");
}

// Contrast therapy = both a heat modality and a cold modality available on site.
export function hasContrast(s: Studio): boolean {
  const hasCold = hasColdPlunge(s) || mods(s).includes("cryo");
  return hasSauna(s) && hasCold;
}

export type Vertical = "cold-plunge" | "sauna" | "infrared-sauna" | "contrast-therapy";

export const VERTICALS: Record<
  Vertical,
  { label: string; noun: string; predicate: (s: Studio) => boolean }
> = {
  "cold-plunge": { label: "Cold Plunge", noun: "cold plunge", predicate: hasColdPlunge },
  sauna: { label: "Sauna", noun: "sauna", predicate: hasSauna },
  "infrared-sauna": { label: "Infrared Sauna", noun: "infrared sauna", predicate: hasInfrared },
  "contrast-therapy": { label: "Contrast Therapy", noun: "contrast therapy", predicate: hasContrast },
};

// ---- Queries -------------------------------------------------------------

export function studiosInMetro(metro: Metro | string): Studio[] {
  const key = typeof metro === "string" ? metro : metro.metro;
  return STUDIOS.filter((s) => s.metro === key);
}

export function studiosForVertical(metro: Metro, v: Vertical): Studio[] {
  return studiosInMetro(metro).filter(VERTICALS[v].predicate);
}

export function studiosWithDayPass(metro: Metro): Studio[] {
  return studiosInMetro(metro).filter(
    (s) => present(s.day_pass_price_usd) || s.access === "day_pass" || s.access === "drop_in",
  );
}

export function studiosCommunal(metro: Metro): Studio[] {
  return studiosInMetro(metro).filter(
    (s) => s.format === "communal" || s.session_style === "communal" || s.access === "communal",
  );
}

export function studiosOpenLate(metro: Metro): Studio[] {
  return studiosInMetro(metro).filter((s) => Boolean(s.access === "open_late"));
}

export function studiosInNeighborhood(metro: Metro, neighborhood: string): Studio[] {
  return studiosInMetro(metro).filter(
    (s) => present(s.neighborhood) && (s.neighborhood as string) === neighborhood,
  );
}

export function neighborhoodsInMetro(metro: Metro): string[] {
  const set = new Set<string>();
  for (const s of studiosInMetro(metro)) {
    if (present(s.neighborhood)) set.add(s.neighborhood as string);
  }
  return Array.from(set).sort();
}

// ---- Guardrail -----------------------------------------------------------
// A directory page is indexable only when backed by >= minStudiosToIndex real studios.
// Below that it may still render (so the URL resolves) but must be noindex.
// Zero studios => caller should not generate the route at all.

export function isIndexable(count: number): boolean {
  return count >= SITE.minStudiosToIndex;
}

export function robotsFor(count: number) {
  return isIndexable(count)
    ? { index: true, follow: true }
    : { index: false, follow: true };
}
