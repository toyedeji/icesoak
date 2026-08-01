import type { Question, RiskTier } from "./types";

/**
 * What each editorial risk tier is allowed to render.
 *
 * The rule these encode, from the 2026-08-01 health-claims audit: the
 * "Practice at Home" affiliate block used to append to every guide regardless
 * of subject, so a page about autoimmune thyroid disease ended with a
 * $1,290–$4,990 cold plunge tub, and a page explaining why 40°F is dangerous
 * for people with cardiovascular disease ended by selling cold plunge hardware.
 * Disclosure was present and adjacent; placement was the problem.
 *
 * Both predicates take the tier as it actually arrives — possibly undefined,
 * because the scraper writes bodyless stubs with no tier at all. Affiliate
 * rendering therefore requires an EXPLICIT C, D or E. Anything unrecognised,
 * missing, or malformed suppresses the block. This is the direction that fails
 * safe: the cost of a false suppression is a missed commission, the cost of a
 * false render is hardware sold under a disease query.
 */

const AFFILIATE_TIERS: ReadonlySet<string> = new Set<RiskTier>(["C", "D", "E"]);
const DISCLAIMER_TIERS: ReadonlySet<string> = new Set<RiskTier>(["A", "B"]);

export function showsAffiliate(tier: Question["risk_tier"]): boolean {
  return typeof tier === "string" && AFFILIATE_TIERS.has(tier);
}

export function showsDisclaimer(tier: Question["risk_tier"]): boolean {
  return typeof tier === "string" && DISCLAIMER_TIERS.has(tier);
}
