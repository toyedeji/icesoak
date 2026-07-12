import type { Metadata } from "next";
import { notFound } from "next/navigation";
import CollectionView from "@/components/CollectionView";
import AffiliateSection from "@/components/AffiliateSection";
import { METROS, metroBySlug } from "./data";
import { studiosForVertical, isIndexable, VERTICALS, type Vertical } from "./studios";
import { cityCapsule, cityDescription } from "./copy";
import { pageMetadata, clamp } from "./seo";
import { itemListSchema, breadcrumbSchema, type Crumb } from "./jsonld";

export interface CityParams {
  city: string;
}

function basePath(v: Vertical, slug: string) {
  return `/${v}/${slug}/`;
}

// Only cold-plunge and sauna city pages carry the "Practice at Home" affiliate
// section — infrared-sauna and contrast-therapy pages are unaffected.
function affiliateTypeFor(v: Vertical): "cold_plunge" | "sauna" | null {
  if (v === "cold-plunge") return "cold_plunge";
  if (v === "sauna") return "sauna";
  return null;
}

// Generate a page for every metro that has at least one qualifying studio for
// this vertical. Metros with zero qualifying studios are omitted (404), never
// shipped as empty doorway pages.
export function verticalStaticParams(v: Vertical): CityParams[] {
  return METROS.filter((m) => studiosForVertical(m, v).length > 0).map((m) => ({
    city: m.slug,
  }));
}

export function verticalMetadata(v: Vertical, params: CityParams): Metadata {
  const metro = metroBySlug(params.city);
  if (!metro) return {};
  const studios = studiosForVertical(metro, v);
  const label = VERTICALS[v].label;
  return pageMetadata({
    title: `${label} in ${metro.name}, ${metro.state}`,
    description: clamp(cityDescription(metro, v, studios)),
    path: basePath(v, metro.slug),
    index: isIndexable(studios.length),
  });
}

export function VerticalCityPage(v: Vertical, params: CityParams) {
  const metro = metroBySlug(params.city);
  if (!metro) notFound();
  const studios = studiosForVertical(metro, v);
  if (studios.length === 0) notFound();

  const label = VERTICALS[v].label;
  const path = basePath(v, metro.slug);
  const indexable = isIndexable(studios.length);

  const crumbs: Crumb[] = [
    { name: "Home", path: "/" },
    { name: label, path: `/${v}/${metro.slug}/` },
    { name: `${metro.name}, ${metro.state}`, path },
  ];

  const jsonLd = [
    breadcrumbSchema(crumbs),
    itemListSchema(studios, `${label} studios in ${metro.name}, ${metro.state}`),
  ];

  const affiliateType = affiliateTypeFor(v);

  return (
    <CollectionView
      crumbs={crumbs}
      h1={`${label} Studios in ${metro.name}, ${metro.state}`}
      capsule={cityCapsule(metro, v, studios)}
      studios={studios}
      center={{ lat: metro.lat, lng: metro.lng }}
      jsonLd={jsonLd}
      indexable={indexable}
      intro={
        <p className="lead">{metro.blurb}</p>
      }
    >
      {affiliateType && <AffiliateSection type={affiliateType} />}
      <SiblingLinks v={v} citySlug={metro.slug} cityName={metro.name} />
    </CollectionView>
  );
}

// Internal-link silo: cross-link the four modality views for the same metro.
function SiblingLinks({
  v,
  citySlug,
  cityName,
}: {
  v: Vertical;
  citySlug: string;
  cityName: string;
}) {
  const others = (Object.keys(VERTICALS) as Vertical[]).filter((k) => k !== v);
  return (
    <section className="section">
      <h2>More recovery options in {cityName}</h2>
      <div className="tiles">
        {others.map((k) => (
          <a key={k} className="tile" href={`/${k}/${citySlug}/`}>
            <strong>{VERTICALS[k].label}</strong>
            <span>{cityName} studios</span>
          </a>
        ))}
      </div>
    </section>
  );
}
