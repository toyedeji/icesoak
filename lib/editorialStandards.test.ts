import { describe, expect, it } from "vitest";
import { SITE, CORRECTIONS_MAILBOX_VERIFIED } from "./site";

// ---------------------------------------------------------------------------
// The second half of this file IS EXPECTED TO FAIL until the corrections
// mailbox exists. Same reasoning as lib/disclaimer.test.ts: it lives in
// `npm test`, not in scripts/assert-build.mjs, so it does not block the deploy.
// ---------------------------------------------------------------------------

describe("byline honesty", () => {
  it("no longer attributes guides to a fictional editorial body", () => {
    expect(SITE.editor).not.toMatch(/editorial/i);
  });
});

describe("corrections address", () => {
  it("is a real mailbox, not a promise", () => {
    // `dig MX icesoak.com` returned nothing on 2026-08-01, so this address
    // bounces. /editorial-standards tells readers corrections get fixed or
    // removed — an address that silently drops them makes that a lie, which is
    // the same class of problem as the byline this page exists to explain.
    //
    // To close: configure MX for icesoak.com, send a test message to
    // SITE.corrections, confirm delivery, then set
    // CORRECTIONS_MAILBOX_VERIFIED = true in lib/site.ts.
    expect(
      CORRECTIONS_MAILBOX_VERIFIED,
      `${SITE.corrections} has not been verified deliverable — icesoak.com had no MX records on 2026-08-01`,
    ).toBe(true);
  });

  it("is on the site's own domain", () => {
    expect(SITE.corrections.endsWith(`@${SITE.domain}`)).toBe(true);
  });
});
