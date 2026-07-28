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

/**
 * A guide is "published" only when it has actual body prose.
 *
 * questions.json is written by two pipelines: scraper/scrape.py harvests
 * question stubs (slug/question/type/metro only), and a separate content pass
 * fills in capsule/sections/author. Between those two steps a guide is a live
 * URL with nothing on it. Every guide on the site was in that state from
 * 2026-07-06 until now, because the scraper overwrote the content pass's work.
 *
 * Bodyless guides stay reachable but are served noindex and kept out of the
 * sitemap, so Google drops them rather than indexing them as thin content. The
 * moment a body is written they flip back to indexable with no code change.
 */
export function hasGuideBody(q: Question): boolean {
  return Array.isArray(q.sections) && q.sections.some((s) => s?.body?.trim());
}

/** Guides with real bodies — the ones safe to index. */
export const PUBLISHED_QUESTIONS: Question[] = QUESTIONS.filter(hasGuideBody);

// Build-time guard. Deliberately a loud warning rather than a hard failure:
// every guide has been bodyless since 2026-07-06, so throwing here would have
// blocked legitimate studio-data deploys too. The hard stop belongs upstream in
// scraper/scrape.py, which is what actually destroys the content.
if (typeof window === "undefined") {
  const bodyless = QUESTIONS.filter((q) => !hasGuideBody(q));
  if (QUESTIONS.length === 0) {
    console.warn(
      "\n[icesoak] ⚠  questions.json contains ZERO guides.\n" +
        "    generateStaticParams() will emit no guide routes and every /guides/* URL\n" +
        "    will 404. This is what commit f5880df (2026-07-19) did.\n",
    );
  } else if (bodyless.length) {
    console.warn(
      `\n[icesoak] ⚠  ${bodyless.length}/${QUESTIONS.length} guides have no body prose.\n` +
        "    These are served noindex,follow and excluded from the sitemap.\n" +
        bodyless.map((q) => `      - ${q.slug}`).join("\n") +
        "\n",
    );
  }
}
