// Central site configuration. Primary domain is icesoak.com; theicesoak.com 301s here.
export const SITE = {
  name: "IceSoak",
  domain: "icesoak.com",
  baseUrl: "https://icesoak.com",
  tagline: "Cold plunge, sauna & contrast-therapy studio directory",
  description:
    "IceSoak is a directory of cold plunge, sauna, and contrast-therapy studios, with verified locations, modalities, and factual recovery guides.",
  // "IceSoak Editorial" until 2026-08-01. There is no editorial team, no named
  // reviewer and no medical review process, and attributing unreviewed health
  // content to a fictional editorial body on a monetized page is the version of
  // this that reads worst in a dispute. See /editorial-standards.
  editor: "IceSoak",
  // Where corrections go. /editorial-standards promises a reply address, so
  // this one has to actually receive mail.
  //
  // UNVERIFIED as of 2026-08-01: `dig MX icesoak.com` returns nothing, so the
  // domain has no mail configured and this address currently bounces. Publishing
  // a corrections contact that silently discards corrections is the same failure
  // as the fictional editorial byline, so lib/editorialStandards.test.ts fails
  // until CORRECTIONS_MAILBOX_VERIFIED is flipped. Configure MX, send a test
  // message, then flip it.
  corrections: "corrections@icesoak.com",
  // Minimum real studios required for a directory page to be indexable (anti-doorway guardrail).
  minStudiosToIndex: 1,
} as const;

export const CORRECTIONS_MAILBOX_VERIFIED = false;

// Absolute URL helper used for canonicals, sitemaps, and JSON-LD @id values.
export function abs(path: string): string {
  if (!path.startsWith("/")) path = "/" + path;
  return SITE.baseUrl + path;
}
