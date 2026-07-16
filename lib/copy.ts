import type { Studio, Metro } from "./types";
import type { Vertical } from "./studios";
import { VERTICALS } from "./studios";

// Builds factual answer capsules that lead with REAL numbers (studio counts) and
// REAL brand names from the data — no marketing language. Kept ~40–60 words.

function uniqueBrands(studios: Studio[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const s of studios) {
    const b = s.brand && s.brand.trim();
    if (b && !seen.has(b)) {
      seen.add(b);
      out.push(b);
    }
  }
  return out;
}

function brandClause(studios: Studio[]): string {
  const brands = uniqueBrands(studios);
  if (brands.length === 0) return "";
  if (brands.length === 1) return ` from ${brands[0]}`;
  if (brands.length === 2) return ` from ${brands[0]} and ${brands[1]}`;
  return ` from brands including ${brands[0]}, ${brands[1]}, and ${brands[2]}`;
}

function cityList(studios: Studio[]): string {
  const cities = Array.from(new Set(studios.map((s) => s.city).filter(Boolean)));
  if (cities.length <= 1) return "";
  if (cities.length === 2) return ` in ${cities[0]} and ${cities[1]}`;
  return ` across ${cities.slice(0, 3).join(", ")} and nearby cities`;
}

export function cityCapsule(metro: Metro, v: Vertical, studios: Studio[]): string {
  const n = studios.length;
  const noun = VERTICALS[v].noun;
  const where = `the ${metro.name} metro`;
  if (n === 0) {
    return `IceSoak is tracking ${noun} studios in ${where}. No verified locations meet our listing threshold yet. Check back as the directory expands, or explore nearby modalities and our factual ${noun} guides in the meantime.`;
  }
  const studioWord = n === 1 ? "studio" : "studios";
  return (
    `IceSoak lists ${n} verified ${noun} ${studioWord} in ${where}${brandClause(studios)}` +
    `${cityList(studios)}. Each listing shows modalities, location, and a last-verified date. ` +
    `Use the map and filters to compare options, or read our guides on ${noun} temperature, timing, and safety.`
  );
}

export function cityDescription(metro: Metro, v: Vertical, studios: Studio[]): string {
  const noun = VERTICALS[v].noun;
  const n = studios.length;
  if (n === 0) {
    return `${VERTICALS[v].label} studios in ${metro.name}, ${metro.state}. IceSoak tracks verified ${noun} locations with modalities, maps, and last-verified dates.`;
  }
  return `Find and compare ${n} verified ${noun} ${n === 1 ? "studio" : "studios"} in ${metro.name}, ${metro.state}. Browse locations, modalities, and nearby options on IceSoak.`;
}

export function bestCapsule(metro: Metro, studios: Studio[]): string {
  const n = studios.length;
  return (
    `IceSoak tracks ${n} cold plunge ${n === 1 ? "studio" : "studios"} in the ${metro.name} metro` +
    `${brandClause(studios)}. This list is ranked by verification completeness and available data, not paid placement. ` +
    `Each entry links to modalities, location, and a last-verified date so you can compare on facts.`
  );
}
