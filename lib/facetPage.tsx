import type { Metadata } from "next";
import { notFound } from "next/navigation";
import CollectionView from "@/components/CollectionView";
import { METROS, metroBySlug } from "./data";
import {
  studiosForVertical,
  studiosWithDayPass,
  studiosCommunal,
  studiosOpenLate,
  studiosInNeighborhood,
  neighborhoodsInMetro,
  isIndexable,
} from "./studios";
import type { Studio, Metro } from "./types";
import { pageMetadata, clamp } from "./seo";
import { itemListSchema, breadcrumbSchema, type Crumb } from "./jsonld";
import { slugify } from "./format";

export type Facet = "day-pass" | "communal" | "open-late";

const FACETS: Record<
  Facet,
  { label: string; phrase: string; select: (m: Metro) => Studio[] }
> = {
  "day-pass": {
    label: "Day Pass",
    phrase: "offer day passes or drop-in access",
    select: studiosWithDayPass,
  },
  communal: {
    label: "Communal",
    phrase: "have communal cold-plunge sessions",
    select: studiosCommunal,
  },
  "open-late": {
    label: "Open Late",
    phrase: "stay open late",
    select: studiosOpenLate,
  },
};

// Only cold-plunge studios matching the facet count toward the page.
function facetStudios(metro: Metro, facet: Facet): Studio[] {
  const cold = new Set(studiosForVertical(metro, "cold-plunge").map((s) => s.id));
  return FACETS[facet].select(metro).filter((s) => cold.has(s.id));
}

// One page per metro (static export needs a non-empty param set). Pages with
// fewer than the threshold render as noindex, so thin facets never get indexed
// but the template still exists and activates as data grows.
export function facetStaticParams(_facet: Facet) {
  return METROS.map((m) => ({ city: m.slug }));
}

export function facetMetadata(facet: Facet, params: { city: string }): Metadata {
  const metro = metroBySlug(params.city);
  if (!metro) return {};
  const studios = facetStudios(metro, facet);
  const f = FACETS[facet];
  return pageMetadata({
    title: `${f.label} Cold Plunge in ${metro.name}, ${metro.state}`,
    description: clamp(
      `${studios.length} cold plunge ${studios.length === 1 ? "studio" : "studios"} that ${f.phrase} in ${metro.name}, ${metro.state}. Verified listings on IceSoak.`,
    ),
    path: `/cold-plunge/${metro.slug}/${facet}/`,
    index: isIndexable(studios.length),
  });
}

export function FacetPage(facet: Facet, params: { city: string }) {
  const metro = metroBySlug(params.city);
  if (!metro) notFound();
  const studios = facetStudios(metro, facet);
  const f = FACETS[facet];
  const path = `/cold-plunge/${metro.slug}/${facet}/`;
  const crumbs: Crumb[] = [
    { name: "Home", path: "/" },
    { name: "Cold Plunge", path: `/cold-plunge/${metro.slug}/` },
    { name: `${metro.name}, ${metro.state}`, path: `/cold-plunge/${metro.slug}/` },
    { name: f.label, path },
  ];
  const capsule =
    studios.length === 0
      ? `IceSoak has not yet verified cold plunge studios that ${f.phrase} in the ${metro.name} metro. This page will populate as access details are confirmed. In the meantime, browse all cold plunge studios in ${metro.name}.`
      : `IceSoak lists ${studios.length} cold plunge ${studios.length === 1 ? "studio" : "studios"} that ${f.phrase} in the ${metro.name} metro. Each listing shows modalities, location, and a last-verified date so you can confirm access details before visiting.`;
  return (
    <CollectionView
      crumbs={crumbs}
      h1={`${f.label} Cold Plunge in ${metro.name}, ${metro.state}`}
      capsule={capsule}
      studios={studios}
      center={{ lat: metro.lat, lng: metro.lng }}
      jsonLd={[
        breadcrumbSchema(crumbs),
        itemListSchema(studios, `${f.label} cold plunge in ${metro.name}`),
      ]}
      indexable={isIndexable(studios.length)}
    />
  );
}

// ---- Neighborhood pages (dense metros only — data-driven) -----------------

export function neighborhoodStaticParams() {
  const out: { city: string; neighborhood: string }[] = [];
  for (const m of METROS) {
    for (const n of neighborhoodsInMetro(m)) {
      // Only emit when the neighborhood itself is backed by >= threshold studios.
      if (studiosInNeighborhood(m, n).length >= 1) {
        out.push({ city: m.slug, neighborhood: slugify(n) });
      }
    }
  }
  return out;
}

function resolveNeighborhood(metro: Metro, slug: string): string | undefined {
  return neighborhoodsInMetro(metro).find((n) => slugify(n) === slug);
}

export function neighborhoodMetadata(params: { city: string; neighborhood: string }): Metadata {
  const metro = metroBySlug(params.city);
  if (!metro) return {};
  const name = resolveNeighborhood(metro, params.neighborhood);
  if (!name) return {};
  const studios = studiosInNeighborhood(metro, name);
  return pageMetadata({
    title: `Cold Plunge in ${name}, ${metro.name}`,
    description: clamp(
      `${studios.length} cold plunge ${studios.length === 1 ? "studio" : "studios"} in ${name}, ${metro.name}, ${metro.state}. Verified listings on IceSoak.`,
    ),
    path: `/cold-plunge/${metro.slug}/${params.neighborhood}/`,
    index: isIndexable(studios.length),
  });
}

export function NeighborhoodPage(params: { city: string; neighborhood: string }) {
  const metro = metroBySlug(params.city);
  if (!metro) notFound();
  const name = resolveNeighborhood(metro, params.neighborhood);
  if (!name) notFound();
  const studios = studiosInNeighborhood(metro, name);
  if (studios.length === 0) notFound();
  const path = `/cold-plunge/${metro.slug}/${params.neighborhood}/`;
  const crumbs: Crumb[] = [
    { name: "Home", path: "/" },
    { name: "Cold Plunge", path: `/cold-plunge/${metro.slug}/` },
    { name: `${metro.name}, ${metro.state}`, path: `/cold-plunge/${metro.slug}/` },
    { name, path },
  ];
  return (
    <CollectionView
      crumbs={crumbs}
      h1={`Cold Plunge in ${name}, ${metro.name}`}
      capsule={`IceSoak lists ${studios.length} cold plunge ${studios.length === 1 ? "studio" : "studios"} in ${name}, part of the ${metro.name} metro. Each listing shows modalities, location, and a last-verified date.`}
      studios={studios}
      center={{ lat: metro.lat, lng: metro.lng }}
      jsonLd={[
        breadcrumbSchema(crumbs),
        itemListSchema(studios, `Cold plunge in ${name}, ${metro.name}`),
      ]}
      indexable={isIndexable(studios.length)}
    />
  );
}
