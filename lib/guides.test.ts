import { describe, expect, it } from "vitest";
import { QUESTIONS, PUBLISHED_QUESTIONS, hasGuideBody, questionBySlug } from "./data";
import { GUIDE_FAQS } from "./guideFAQs";

// ---------------------------------------------------------------------------
// These assert against the real questions.json the build will consume.
//
// Context: from 2026-07-06 until 2026-07-28 every guide on the site rendered a
// title, an empty "Quick answer", and nothing else, because scraper/scrape.py
// overwrote questions.json with four-field stubs on every run. On 2026-07-19 a
// failed harvest wrote a literal [], which would have turned all 52 guide URLs
// into 404s on the next deploy. Nothing caught either event.
// ---------------------------------------------------------------------------

describe("questions.json integrity", () => {
  it("is not empty — an empty file 404s every guide URL", () => {
    // The precise failure mode of commit f5880df. generateStaticParams() maps
    // over QUESTIONS, so zero questions means zero guide routes are emitted.
    expect(QUESTIONS.length).toBeGreaterThan(0);
  });

  it("emits a non-zero number of static params", () => {
    // Mirrors app/guides/[slug]/page.tsx generateStaticParams().
    const params = QUESTIONS.map((q) => ({ slug: q.slug }));
    expect(params.length).toBeGreaterThan(0);
    expect(params.every((p) => typeof p.slug === "string" && p.slug.length > 0)).toBe(true);
  });

  it("has no duplicate slugs", () => {
    const slugs = QUESTIONS.map((q) => q.slug);
    expect(new Set(slugs).size).toBe(slugs.length);
  });

  it("every record carries the scraper-owned fields", () => {
    for (const q of QUESTIONS) {
      expect(typeof q.slug, q.slug).toBe("string");
      expect(typeof q.question, q.slug).toBe("string");
      expect(q.question.length, q.slug).toBeGreaterThan(0);
    }
  });
});

describe("published guides have real bodies", () => {
  it("at least 25 guides have body prose (the recovered set, less the removals)", () => {
    // 32 bodies were recovered on 2026-07-28. Seven were dropped on 2026-08-01
    // by the health-claims audit — two off-topic Dallas travel pages, three
    // duplicates, and two about a named living person. See guide_denylist.json.
    expect(PUBLISHED_QUESTIONS.length).toBeGreaterThanOrEqual(25);
  });

  it("no PUBLISHED guide has an empty body", () => {
    // The headline assertion. A guide counted as published must have prose.
    for (const q of PUBLISHED_QUESTIONS) {
      expect(hasGuideBody(q), `${q.slug} is published but has no body`).toBe(true);
      const words = (q.sections ?? []).map((s) => s.body).join(" ").trim().split(/\s+/).length;
      expect(words, `${q.slug} body is suspiciously short`).toBeGreaterThan(20);
    }
  });

  it("no published guide has an empty section heading or body", () => {
    for (const q of PUBLISHED_QUESTIONS) {
      for (const s of q.sections ?? []) {
        expect(s.h2?.trim(), `${q.slug} has a section with no heading`).toBeTruthy();
        expect(s.body?.trim(), `${q.slug} has a section with no body`).toBeTruthy();
      }
    }
  });

  it("every published guide has a capsule for the Quick answer block", () => {
    for (const q of PUBLISHED_QUESTIONS) {
      expect(q.capsule?.trim(), `${q.slug} has no capsule`).toBeTruthy();
    }
  });

  it("every published guide has an author, so the byline is never a bare 'By'", () => {
    for (const q of PUBLISHED_QUESTIONS) {
      expect(q.author?.trim(), `${q.slug} has no author`).toBeTruthy();
    }
  });
});

describe("bodyless guides are handled, not hidden", () => {
  it("bodyless guides still exist as routes rather than 404ing", () => {
    const bodyless = QUESTIONS.filter((q) => !hasGuideBody(q));
    // They are kept deliberately: the URLs are already indexed and internally
    // linked. They are served noindex,follow instead of being deleted.
    expect(bodyless.length).toBeGreaterThan(0);
    for (const q of bodyless) {
      expect(questionBySlug(q.slug), `${q.slug} must still resolve`).toBeDefined();
    }
  });

  it("hasGuideBody rejects the shapes the scraper actually produced", () => {
    expect(hasGuideBody({ slug: "x" } as never)).toBe(false);
    expect(hasGuideBody({ slug: "x", sections: [] } as never)).toBe(false);
    expect(hasGuideBody({ slug: "x", sections: [{ h2: "H", body: "" }] } as never)).toBe(false);
    expect(hasGuideBody({ slug: "x", sections: [{ h2: "H", body: "   " }] } as never)).toBe(false);
    expect(hasGuideBody({ slug: "x", sections: [{ h2: "H", body: "real" }] } as never)).toBe(true);
  });
});

describe("curated FAQ overlay", () => {
  it("every GUIDE_FAQS key matches a real guide slug", () => {
    // These three hardcoded keys were the only reason one broken page showed an
    // FAQ section and another didn't — worth pinning so they can't rot.
    for (const slug of Object.keys(GUIDE_FAQS)) {
      expect(questionBySlug(slug), `GUIDE_FAQS key "${slug}" matches no guide`).toBeDefined();
    }
  });
});
