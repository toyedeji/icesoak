// studios.json and questions.json live at the REPO ROOT — the single source of
// truth that the scraper (scraper/scrape.py) overwrites on each run.
// metros.json is static site config and stays under data/.
import studiosJson from "@/studios.json";
import questionsJson from "@/questions.json";
import metrosJson from "@/data/metros.json";
import type { Studio, Question, Metro } from "./types";

// Load + normalize. The build must succeed even if data is a stub or empty.
function safeArray<T>(v: unknown): T[] {
  return Array.isArray(v) ? (v as T[]) : [];
}

// Only "active" studios are considered real/listable.
export const STUDIOS: Studio[] = safeArray<Studio>(studiosJson).filter(
  (s) => s && typeof s.id === "string" && (s.status ?? "active") !== "closed",
);

export const QUESTIONS: Question[] = safeArray<Question>(questionsJson).filter(
  (q) => q && typeof q.slug === "string",
);

export const METROS: Metro[] = safeArray<Metro>(metrosJson);

export function metroBySlug(slug: string): Metro | undefined {
  return METROS.find((m) => m.slug === slug);
}

export function metroByKey(key: string): Metro | undefined {
  return METROS.find((m) => m.metro === key);
}

export function studioById(id: string): Studio | undefined {
  return STUDIOS.find((s) => s.id === id);
}

export function questionBySlug(slug: string): Question | undefined {
  return QUESTIONS.find((q) => q.slug === slug);
}
