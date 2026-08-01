import Link from "next/link";
import type { RiskTier } from "@/lib/types";

/**
 * Guide-scoped medical disclaimer. Rendered above the fold on risk_tier A
 * (condition-specific claims) and B (safety thresholds and dosing).
 *
 * This is deliberately NOT the footer line in components/SiteFooter.tsx, which
 * is scoped to studio listings ("Listings are informational…") and does not
 * cover a page about autoimmune thyroid disease or a water-temperature limit.
 *
 * Tier A adds one sentence to the front of the Tier B text. The rest is
 * identical on purpose: the acute cardiovascular warning and the stop-if-you-
 * feel-unwell instruction apply just as much to a temperature threshold as to a
 * named condition.
 */
export const PLACEHOLDER_COPY = false;

export default function MedicalDisclaimer({ tier }: { tier: RiskTier }) {
  return (
    <aside className="disclaimer" role="note" aria-label="Medical disclaimer">
      <p>
        <strong>Not medical advice.</strong>{" "}
        {tier === "A" && (
          <>
            This page discusses a specific medical condition and is not a
            substitute for care from a clinician who knows your history.{" "}
          </>
        )}
        This page is general information compiled from published sources. It has
        not been reviewed by a clinician. Cold water immersion and sauna heat
        both place acute stress on the heart and circulation, and individual
        tolerance varies widely. If you have a heart condition, high or
        unmanaged blood pressure, are pregnant, or take medication affecting
        circulation or body-temperature regulation, talk to your doctor before
        starting. Stop and get out if you feel faint, dizzy, numb, or unwell.{" "}
        <Link href="/editorial-standards/">How we write these guides</Link>
      </p>
    </aside>
  );
}
