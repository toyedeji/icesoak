import type { Studio, Question, Metro } from "./types";
import { SITE, abs } from "./site";
import { present, val, modalityLabel } from "./format";

// All builders return plain JSON-serializable objects. Undefined fields are
// stripped by prune() so we never emit null/empty values into structured data.

function prune<T>(obj: T): T {
  if (Array.isArray(obj)) {
    return obj.map(prune).filter((v) => v !== undefined) as unknown as T;
  }
  if (obj && typeof obj === "object") {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
      if (v === undefined || v === null) continue;
      const pv = prune(v);
      if (pv === undefined) continue;
      if (typeof pv === "string" && pv.trim() === "") continue;
      if (Array.isArray(pv) && pv.length === 0) continue;
      out[k] = pv;
    }
    return out as T;
  }
  return obj;
}

export function organizationSchema() {
  return prune({
    "@context": "https://schema.org",
    "@type": "Organization",
    "@id": abs("/#organization"),
    name: SITE.name,
    url: SITE.baseUrl,
    description: SITE.description,
  });
}

export function websiteSchema() {
  return prune({
    "@context": "https://schema.org",
    "@type": "WebSite",
    "@id": abs("/#website"),
    name: SITE.name,
    url: SITE.baseUrl,
    publisher: { "@id": abs("/#organization") },
  });
}

export interface Crumb {
  name: string;
  path: string;
}

export function breadcrumbSchema(crumbs: Crumb[]) {
  return prune({
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: crumbs.map((c, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: c.name,
      item: abs(c.path),
    })),
  });
}

// A studio is a health/wellness business. Only emit fields that are present.
export function studioSchema(s: Studio) {
  const url = abs(`/studio/${s.id}/`);
  return prune({
    "@context": "https://schema.org",
    "@type": "HealthAndBeautyBusiness",
    "@id": url + "#business",
    name: s.name,
    url,
    // Recommended optional fields — emitted ONLY when the source data exists.
    telephone: val(s.telephone) ?? val(s.phone),
    image: val(s.image),
    priceRange: present(s.day_pass_price_usd)
      ? `$${Math.round(Number(s.day_pass_price_usd))}`
      : undefined,
    openingHours: present(s.opening_hours)
      ? (s.opening_hours as string[] | string)
      : undefined,
    address: present(s.address) || present(s.city)
      ? {
          "@type": "PostalAddress",
          streetAddress: val(s.address),
          addressLocality: val(s.city),
          addressRegion: val(s.state),
          addressCountry: "US",
        }
      : undefined,
    geo:
      present(s.lat) && present(s.lng)
        ? { "@type": "GeoCoordinates", latitude: s.lat, longitude: s.lng }
        : undefined,
    sameAs: present(s.website) ? [s.website] : undefined,
    brand: val(s.brand),
    amenityFeature: present(s.modalities)
      ? (s.modalities as string[]).map((m) => ({
          "@type": "LocationFeatureSpecification",
          name: modalityLabel(m),
          value: true,
        }))
      : undefined,
    aggregateRating:
      present(s.google_rating) && present(s.google_reviews_count)
        ? {
            "@type": "AggregateRating",
            ratingValue: s.google_rating,
            reviewCount: s.google_reviews_count,
          }
        : undefined,
  });
}

// City / list pages: ItemList of studios.
export function itemListSchema(studios: Studio[], name: string) {
  return prune({
    "@context": "https://schema.org",
    "@type": "ItemList",
    name,
    numberOfItems: studios.length,
    itemListElement: studios.map((s, i) => ({
      "@type": "ListItem",
      position: i + 1,
      url: abs(`/studio/${s.id}/`),
      name: s.name,
    })),
  });
}

// Guides: FAQPage built from the guide's headline question (answered by its
// answer-capsule + body prose), plus each explicit Q&A entry as its own question.
export function faqSchema(q: Question) {
  const mainEntity = [
    {
      "@type": "Question",
      name: q.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: [q.capsule, ...(q.sections ?? []).map((s) => s.body)].join("\n\n"),
      },
    },
    ...(q.faqs ?? []).map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a },
    })),
  ];
  return prune({
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity,
  });
}

// Article wrapper for guides, with named (non-fabricated) editorial byline.
export function articleSchema(q: Question, path: string) {
  return prune({
    "@context": "https://schema.org",
    "@type": "Article",
    headline: q.question,
    description: q.capsule,
    datePublished: q.updated,
    dateModified: q.updated,
    author: { "@type": "Organization", name: q.author || SITE.editor },
    publisher: { "@id": abs("/#organization") },
    mainEntityOfPage: abs(path),
  });
}

export function metroLabel(m: Metro): string {
  return `${m.name}, ${m.state}`;
}
