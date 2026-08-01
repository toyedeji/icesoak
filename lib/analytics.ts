// GA4 wiring. Mirrors blknomad's src/lib/analytics.ts, which is the working
// reference implementation for this stack.
//
// No affiliate_click event here yet, deliberately. blknomad's went 1 -> 0
// between 2026-07-30 and 2026-08-01 and it is not yet known whether that was a
// single bot or the event itself breaking. Copying an event whose reliability is
// under question would just spread the uncertainty to a second property.

/**
 * The property this site is supposed to report to, pinned in the repo.
 *
 * Pinned rather than trusted-from-env because the failure mode being guarded is
 * NOT "no tag" — a missing tag is obvious the moment anyone opens Realtime. It
 * is a tag present with the WRONG property ID, which looks exactly like success
 * from the site, from the build, and from the pulse collector, while the data
 * lands in someone else's property. A measurement ID is public by construction
 * (it ships in the page HTML), so there is nothing to protect by keeping it out
 * of the repo.
 *
 * scripts/assert-build.mjs asserts this value, the env var, and the ID actually
 * rendered into out/ all agree.
 */
export const EXPECTED_GA4_MEASUREMENT_ID = 'G-YY5Z2JVSGK';

export const GA4_MEASUREMENT_ID = process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID || '';

/** True only when a measurement ID is configured. */
export const ANALYTICS_ENABLED = GA4_MEASUREMENT_ID !== '';

type GtagFn = (
  command: 'event' | 'config' | 'js',
  target: string | Date,
  params?: Record<string, unknown>,
) => void;

declare global {
  interface Window {
    gtag?: GtagFn;
    dataLayer?: unknown[];
  }
}
