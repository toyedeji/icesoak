import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";

// ---------------------------------------------------------------------------
// This started as a deliberately failing scaffold (TASK 4 asked for one, so the
// missing copy could not quietly become permanent). The approved wording landed
// on 2026-08-01 and PLACEHOLDER_COPY was flipped to false, so it now guards
// against regression instead: the specific warnings below were chosen, not
// improvised, and should not be edited away without a decision.
// ---------------------------------------------------------------------------

const SRC = readFileSync(
  path.resolve(__dirname, "../components/MedicalDisclaimer.tsx"),
  "utf8",
);
// JSX wraps prose across lines at whatever column the formatter picks, so
// clause matching runs against a whitespace-normalized copy. Otherwise this
// test breaks on reflow rather than on a change of meaning.
const FLAT = SRC.replace(/\s+/g, " ");

describe("medical disclaimer copy", () => {
  it("is approved copy, not the placeholder scaffold", () => {
    expect(
      /PLACEHOLDER_COPY\s*=\s*false/.test(SRC),
      "MedicalDisclaimer still renders placeholder copy — supply the approved wording " +
        "and set PLACEHOLDER_COPY = false",
    ).toBe(true);
  });

  it("keeps every clause of the approved warning", () => {
    for (const clause of [
      "Not medical advice.",
      "has not been reviewed by a clinician",
      "acute stress on the heart and circulation",
      "high or unmanaged blood pressure",
      "are pregnant",
      "medication affecting circulation or body-temperature regulation",
      "faint, dizzy, numb, or unwell",
    ]) {
      expect(FLAT.includes(clause), `missing approved clause: ${clause}`).toBe(true);
    }
  });

  it("carries the extra Tier A sentence, conditionally", () => {
    // Tier A pages discuss a named condition, and get one sentence more than
    // Tier B. It must be gated on the tier, not rendered unconditionally.
    expect(SRC).toMatch(/tier === "A"/);
    expect(SRC).toContain("discusses a specific medical condition");
  });

  it("points at the editorial standards page", () => {
    expect(SRC).toContain("/editorial-standards/");
  });
});
