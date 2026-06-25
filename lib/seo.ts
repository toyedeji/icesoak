import type { Metadata } from "next";
import { SITE, abs } from "./site";

interface PageSeo {
  title: string;
  description: string;
  path: string;
  index: boolean;
}

// Single source of truth for per-page metadata: templated title/description,
// canonical, robots, and Open Graph. Titles are kept under ~60 chars + brand.
export function pageMetadata({ title, description, path, index }: PageSeo): Metadata {
  const url = abs(path);
  const fullTitle = title.includes(SITE.name) ? title : `${title} | ${SITE.name}`;
  return {
    title: fullTitle,
    description,
    alternates: { canonical: url },
    robots: index
      ? { index: true, follow: true }
      : { index: false, follow: true, googleBot: { index: false, follow: true } },
    openGraph: {
      type: "website",
      siteName: SITE.name,
      title: fullTitle,
      description,
      url,
    },
    twitter: { card: "summary", title: fullTitle, description },
  };
}

export function clamp(s: string, max = 158): string {
  if (s.length <= max) return s;
  return s.slice(0, max - 1).replace(/\s+\S*$/, "") + "…";
}
