// Central site configuration. Primary domain is icesoak.com; theicesoak.com 301s here.
export const SITE = {
  name: "IceSoak",
  domain: "icesoak.com",
  baseUrl: "https://icesoak.com",
  tagline: "Cold plunge, sauna & contrast-therapy studio directory",
  description:
    "IceSoak is a directory of cold plunge, sauna, and contrast-therapy studios, with verified locations, modalities, and factual recovery guides.",
  editor: "IceSoak Editorial",
  // Minimum real studios required for a directory page to be indexable (anti-doorway guardrail).
  minStudiosToIndex: 3,
} as const;

// Absolute URL helper used for canonicals, sitemaps, and JSON-LD @id values.
export function abs(path: string): string {
  if (!path.startsWith("/")) path = "/" + path;
  return SITE.baseUrl + path;
}
