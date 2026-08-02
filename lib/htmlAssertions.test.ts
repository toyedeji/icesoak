import { describe, expect, it } from "vitest";
// @ts-expect-error — plain ESM helper shared with scripts/assert-build.mjs
import {
  normalize,
  hasAffiliate,
  hasDisclaimer,
  hasForbiddenByline,
} from "../scripts/htmlAssertions.mjs";

// ---------------------------------------------------------------------------
// These pin the defect that made every negative assertion in the build gate
// vacuous until 2026-08-01.
//
// React emits an HTML comment around every `{…}` in a text position, so a
// contiguous `includes()` across an interpolation boundary always returns
// false. On a POSITIVE assertion that fails loudly. On a NEGATIVE one — "this
// string must NOT appear" — it passes silently while the string is on the page.
//
// Each fixture below is markup React would actually emit. The "raw" case in
// each pair is what the gate used to do, and is asserted to demonstrate the
// bug is real rather than theoretical.
// ---------------------------------------------------------------------------

describe("normalize", () => {
  it("removes React's interpolation separators", () => {
    expect(normalize("Compiled by <!-- -->IceSoak<!-- --> Editorial")).toBe(
      "Compiled by IceSoak Editorial",
    );
  });

  it("collapses the whitespace React wraps prose across", () => {
    expect(normalize("Not medical\n        advice.")).toBe("Not medical advice.");
  });

  it("removes multi-line comments too", () => {
    expect(normalize("a<!--\n  anything\n-->b")).toBe("ab");
  });
});

describe("forbidden byline survives an interpolation boundary", () => {
  // What `By {q.author} Editorial` renders as when author === "IceSoak".
  const SPLIT = '<p class="byline">By <!-- -->IceSoak<!-- --> Editorial</p>';

  it("the OLD contiguous check missed it — this is the bug", () => {
    expect(SPLIT.includes("IceSoak Editorial")).toBe(false);
  });

  it("the normalized check catches it", () => {
    expect(hasForbiddenByline(SPLIT)).toBe(true);
  });

  it("still passes clean on the byline actually shipped", () => {
    const SHIPPED =
      '<p class="byline">Compiled by <!-- -->IceSoak<!-- --> ·<!-- --> ' +
      '<a href="/editorial-standards/">Not medically reviewed</a> · Last updated August 1, 2026</p>';
    expect(hasForbiddenByline(SHIPPED)).toBe(false);
  });
});

describe("affiliate block survives an interpolation boundary", () => {
  // What `<h2>Practice at {word} Home</h2>` would render as — the shape a
  // future refactor of the heading could produce without anyone noticing the
  // gate had stopped looking.
  const SPLIT = '<section class="affiliate"><h2>Practice at<!-- --> Home</h2></section>';

  it("the OLD contiguous check missed it — this is the bug", () => {
    expect(SPLIT.includes(">Practice at Home<")).toBe(false);
  });

  it("the normalized check catches it", () => {
    expect(hasAffiliate(SPLIT)).toBe(true);
  });

  it("catches the sponsored-link marker on its own", () => {
    // Attribute values never receive separators, so this half was never at
    // risk. Pinned anyway so a refactor cannot quietly drop it.
    expect(hasAffiliate('<a rel="sponsored nofollow noopener" href="#">x</a>')).toBe(true);
  });

  it("does not fire on a page with neither marker", () => {
    expect(hasAffiliate("<article><h2>What is Hashimoto's?</h2></article>")).toBe(false);
  });
});

describe("disclaimer detection", () => {
  it("finds the disclaimer by its aria-label", () => {
    expect(hasDisclaimer('<aside aria-label="Medical disclaimer"><p>x</p></aside>')).toBe(true);
  });

  it("survives attribute reordering across whitespace", () => {
    expect(
      hasDisclaimer('<aside role="note"\n  aria-label="Medical disclaimer">x</aside>'),
    ).toBe(true);
  });

  it("does not fire on a page without one", () => {
    expect(hasDisclaimer("<article>no disclaimer here</article>")).toBe(false);
  });
});
