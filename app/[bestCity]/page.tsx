import type { Metadata } from "next";
import { notFound } from "next/navigation";
import CollectionView from "@/components/CollectionView";
import { METROS, metroBySlug } from "@/lib/data";
import { studiosForVertical, isIndexable } from "@/lib/studios";
import { bestCapsule } from "@/lib/copy";
import { pageMetadata, clamp } from "@/lib/seo";
import { itemListSchema, breadcrumbSchema, type Crumb } from "@/lib/jsonld";

const PREFIX = "best-cold-plunge-";
type P = { params: Promise<{ bestCity: string }> };

// "Best of" lists are doorway-prone. One page is generated per metro (export
// needs a non-empty param set), but a metro is only indexable once it clears the
// >=3 verified-studio threshold; thinner ones render as noindex. This root-level
// dynamic segment is gated by generateStaticParams to ONLY best-cold-plunge-* slugs.
export function generateStaticParams() {
  return METROS.map((m) => ({ bestCity: `${PREFIX}${m.slug}` }));
}

function resolve(slug: string) {
  if (!slug.startsWith(PREFIX)) return undefined;
  const metro = metroBySlug(slug.slice(PREFIX.length));
  if (!metro) return undefined;
  const studios = studiosForVertical(metro, "cold-plunge");
  return { metro, studios, indexable: isIndexable(studios.length) };
}

export async function generateMetadata({ params }: P): Promise<Metadata> {
  const r = resolve((await params).bestCity);
  if (!r) return {};
  return pageMetadata({
    title: `Best Cold Plunge Studios in ${r.metro.name}, ${r.metro.state}`,
    description: clamp(
      `Find and compare ${r.studios.length} verified cold plunge ${r.studios.length === 1 ? "studio" : "studios"} in ${r.metro.name}, ${r.metro.state}. Ranked by verification completeness, not paid placement.`,
    ),
    path: `/${PREFIX}${r.metro.slug}/`,
    index: r.indexable,
  });
}

export default async function Page({ params }: P) {
  const r = resolve((await params).bestCity);
  if (!r) notFound();
  const { metro, studios, indexable } = r;
  const path = `/${PREFIX}${metro.slug}/`;
  const crumbs: Crumb[] = [
    { name: "Home", path: "/" },
    { name: "Cold Plunge", path: `/cold-plunge/${metro.slug}/` },
    { name: `Best in ${metro.name}`, path },
  ];
  return (
    <CollectionView
      crumbs={crumbs}
      h1={`Best Cold Plunge Studios in ${metro.name}, ${metro.state}`}
      capsule={bestCapsule(metro, studios)}
      studios={studios}
      center={{ lat: metro.lat, lng: metro.lng }}
      jsonLd={[
        breadcrumbSchema(crumbs),
        itemListSchema(studios, `Best cold plunge in ${metro.name}, ${metro.state}`),
      ]}
      indexable={indexable}
    />
  );
}
