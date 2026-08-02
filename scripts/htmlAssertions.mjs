/**
 * Helpers for asserting against rendered React output.
 *
 * Extracted from assert-build.mjs so they can be unit-tested directly —
 * lib/htmlAssertions.test.ts pins the behaviour that made every negative
 * assertion in the gate vacuous until 2026-08-01. Importing assert-build.mjs
 * itself would run the whole gate as a side effect, so these live here.
 */

/**
 * Strip React's interpolation separators and collapse whitespace.
 *
 * React emits an HTML comment around every `{…}` in a text position:
 *
 *   source:  Compiled by {q.author} Editorial
 *   output:  Compiled by <!-- -->IceSoak<!-- --> Editorial
 *
 * `html.includes("IceSoak Editorial")` is FALSE on that markup even though the
 * page visibly says it. For a POSITIVE assertion that is merely annoying — it
 * fails loudly and you go look. For a NEGATIVE assertion it is silent and
 * total: the check passes, the gate goes green, and the forbidden string is on
 * the page.
 *
 * Note the boundary of the problem, since it drives what was actually exposed:
 * React does NOT insert separators inside attribute values, so href/rel checks
 * were never at risk. Text children — prose, headings, bylines — were.
 * Normalizing everything removes the need to remember which is which.
 */
export const normalize = (html) =>
  html.replace(/<!--.*?-->/gs, "").replace(/\s+/g, " ");

/**
 * The affiliate block's own heading and the sponsored links it wraps. Matching
 * both means a partial render (heading kept, cards dropped, or vice versa)
 * still trips the gate.
 */
export const AFFILIATE_MARKERS = [">Practice at Home<", 'rel="sponsored'];

export const hasAffiliate = (html) =>
  AFFILIATE_MARKERS.some((m) => normalize(html).includes(m));

export const hasDisclaimer = (html) =>
  normalize(html).includes('aria-label="Medical disclaimer"');

/** The byline this site must never render again. See lib/site.ts. */
export const FORBIDDEN_BYLINE = "IceSoak Editorial";

export const hasForbiddenByline = (html) =>
  normalize(html).includes(FORBIDDEN_BYLINE);
