import { describe, expect, it } from "vitest";
import { showsAffiliate, showsDisclaimer } from "./riskTier";
import { PUBLISHED_QUESTIONS, QUESTIONS, DENIED_GUIDE_SLUGS } from "./data";

// ---------------------------------------------------------------------------
// These cover the DECISION. Whether the decision survives into the shipped HTML
// is a separate question, asserted against out/ by scripts/assert-build.mjs —
// a passing test here plus a broken template would still ship a cold plunge tub
// at the bottom of a page about autoimmune thyroid disease.
// ---------------------------------------------------------------------------

describe("affiliate gating fails closed", () => {
  it("suppresses the block on tiers A and B", () => {
    expect(showsAffiliate("A")).toBe(false);
    expect(showsAffiliate("B")).toBe(false);
  });

  it("renders the block on tiers C, D and E", () => {
    expect(showsAffiliate("C")).toBe(true);
    expect(showsAffiliate("D")).toBe(true);
    expect(showsAffiliate("E")).toBe(true);
  });

  it("suppresses on a missing or unrecognised tier", () => {
    // The scraper writes bodyless stubs with no tier at all, and a future
    // harvest could write junk. Neither may open the gate.
    expect(showsAffiliate(undefined)).toBe(false);
    expect(showsAffiliate("" as never)).toBe(false);
    expect(showsAffiliate("F" as never)).toBe(false);
    expect(showsAffiliate("a" as never)).toBe(false);
    expect(showsAffiliate(null as never)).toBe(false);
  });
});

describe("disclaimer gating", () => {
  it("shows on tiers A and B and nowhere else", () => {
    expect(showsDisclaimer("A")).toBe(true);
    expect(showsDisclaimer("B")).toBe(true);
    expect(showsDisclaimer("C")).toBe(false);
    expect(showsDisclaimer("D")).toBe(false);
    expect(showsDisclaimer("E")).toBe(false);
    expect(showsDisclaimer(undefined)).toBe(false);
  });
});

describe("the tiers assigned in questions.json", () => {
  it("tiers every published guide", () => {
    const untiered = PUBLISHED_QUESTIONS.filter((q) => !q.risk_tier).map((q) => q.slug);
    expect(untiered, "published guides with no risk_tier").toEqual([]);
  });

  it("puts every condition-specific and threshold guide out of affiliate reach", () => {
    // Named explicitly rather than derived, so a tier downgrade has to be
    // argued for in a diff instead of happening quietly.
    const mustSuppress = [
      "does-sauna-help-hashimotos",
      "does-sauna-decrease-bp",
      "can-saunas-help-lower-cholesterol",
      "can-cold-plunge-lower-cortisol",
      "do-cold-plunges-help-with-inflammation",
      "do-ice-baths-reduce-doms",
      "are-cold-plunges-actually-healthy",
      "what-toxins-do-saunas-remove",
      "is-a-40-degree-ice-bath-safe",
      "is-2-degrees-too-cold-for-an-ice-bath",
      "how-long-do-you-sit-in-an-ice-bath",
      "what-is-the-1-10-1-rule-in-cold-water",
      "who-should-not-do-contrast-therapy",
    ];
    for (const slug of mustSuppress) {
      const q = PUBLISHED_QUESTIONS.find((x) => x.slug === slug);
      expect(q, `${slug} is missing from questions.json`).toBeDefined();
      expect(showsAffiliate(q!.risk_tier), `${slug} would render the affiliate block`).toBe(false);
      expect(showsDisclaimer(q!.risk_tier), `${slug} would render no disclaimer`).toBe(true);
    }
  });

  it("still monetizes the neutral commercial guide", () => {
    // The gate is supposed to be topical, not a blanket kill switch.
    const q = PUBLISHED_QUESTIONS.find((x) => x.slug === "what-is-the-average-cost-of-a-cold-plunge");
    expect(q).toBeDefined();
    expect(showsAffiliate(q!.risk_tier)).toBe(true);
  });
});

describe("guide denylist", () => {
  it("holds the seven guides dropped on 2026-08-01", () => {
    expect(DENIED_GUIDE_SLUGS.size).toBe(7);
  });

  it("keeps denylisted slugs out of QUESTIONS entirely", () => {
    // QUESTIONS feeds generateStaticParams(). A denylisted slug here means a
    // static file gets written, which shadows the force = false 301.
    const leaked = QUESTIONS.filter((q) => DENIED_GUIDE_SLUGS.has(q.slug)).map((q) => q.slug);
    expect(leaked).toEqual([]);
  });
});
