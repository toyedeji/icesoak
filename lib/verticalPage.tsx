import type { Metadata } from "next";
import { notFound } from "next/navigation";
import CollectionView from "@/components/CollectionView";
import AffiliateSection from "@/components/AffiliateSection";
import InternalLinks from "@/components/InternalLinks";
import { METROS, metroBySlug } from "./data";
import { studiosForVertical, isIndexable, VERTICALS, type Vertical } from "./studios";
import { cityCapsule, cityDescription } from "./copy";
import { pageMetadata, clamp } from "./seo";
import { itemListSchema, breadcrumbSchema, type Crumb } from "./jsonld";
import { modalityLabel, present, usd } from "./format";
import type { Studio, Metro } from "./types";

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
    title: `${label} Studios in ${metro.name}, ${metro.state}`,
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
  const noun = VERTICALS[v].noun;

  const crumbs: Crumb[] = [
    { name: "Home", path: "/" },
    { name: label, path: `/${v}/${metro.slug}/` },
    { name: `${metro.name}, ${metro.state}`, path },
  ];

  const stats = cityStats(studios);
  const top3 = topByReviews(studios, 3);
  const faqs = cityFaqs(metro, v, studios, stats, top3);
  const faqLd = faqPageJsonLd(faqs);

  const jsonLd = [
    breadcrumbSchema(crumbs),
    itemListSchema(studios, `${label} studios in ${metro.name}, ${metro.state}`),
    faqLd,
  ].filter(Boolean);

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
      intro={<p className="lead">{metro.blurb}</p>}
    >
      <CityStatsSection metro={metro} noun={noun} stats={stats} />
      {top3.length > 0 && (
        <TopStudiosSection metro={metro} label={label} studios={top3} />
      )}
      {faqs.length > 0 && <CityFaqSection faqs={faqs} />}
      <InternalLinks type="city" slug={metro.slug} />
      {affiliateType && <AffiliateSection type={affiliateType} />}
      <SiblingLinks v={v} citySlug={metro.slug} cityName={metro.name} />
    </CollectionView>
  );
}

// ─── Aggregation helpers (derive per-metro facts from populated fields only) ───

interface CityStatsShape {
  studioCount: number;
  cities: string[];
  neighborhoods: string[];
  modalityCounts: { code: string; count: number }[];
  priceMin?: number;
  priceMax?: number;
  priceCount: number;
  ratingAvg?: number;
  ratingCount: number;
}

function cityStats(studios: Studio[]): CityStatsShape {
  const cities = uniq(studios.map((s) => (present(s.city) ? (s.city as string) : ""))).filter(
    Boolean,
  );
  const neighborhoods = uniq(
    studios.map((s) => (present(s.neighborhood) ? (s.neighborhood as string) : "")),
  ).filter(Boolean);

  const modCounts = new Map<string, number>();
  for (const s of studios) {
    for (const m of s.modalities ?? []) {
      modCounts.set(m, (modCounts.get(m) ?? 0) + 1);
    }
  }
  const modalityCounts = Array.from(modCounts.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([code, count]) => ({ code, count }));

  const prices = studios
    .map((s) => (present(s.day_pass_price_usd) ? Number(s.day_pass_price_usd) : NaN))
    .filter((n) => Number.isFinite(n));
  const ratings = studios
    .map((s) => (present(s.google_rating) ? Number(s.google_rating) : NaN))
    .filter((n) => Number.isFinite(n));

  return {
    studioCount: studios.length,
    cities,
    neighborhoods,
    modalityCounts,
    priceMin: prices.length ? Math.min(...prices) : undefined,
    priceMax: prices.length ? Math.max(...prices) : undefined,
    priceCount: prices.length,
    ratingAvg: ratings.length
      ? Math.round((ratings.reduce((a, b) => a + b, 0) / ratings.length) * 10) / 10
      : undefined,
    ratingCount: ratings.length,
  };
}

function topByReviews(studios: Studio[], n: number): Studio[] {
  return studios
    .filter((s) => present(s.google_reviews_count) && (s.google_reviews_count as number) > 0)
    .slice()
    .sort(
      (a, b) => (b.google_reviews_count as number) - (a.google_reviews_count as number),
    )
    .slice(0, n);
}

function cityFaqs(
  metro: Metro,
  v: Vertical,
  studios: Studio[],
  stats: CityStatsShape,
  top3: Studio[],
): { q: string; a: string }[] {
  const noun = VERTICALS[v].noun;
  const label = VERTICALS[v].label.toLowerCase();
  const where = `${metro.name}, ${metro.state}`;
  const out: { q: string; a: string }[] = [];

  out.push({
    q: `How many ${label} studios are in ${metro.name}?`,
    a: `IceSoak tracks ${stats.studioCount} verified ${noun} ${stats.studioCount === 1 ? "studio" : "studios"} in the ${metro.name} metro area.`,
  });

  if (stats.priceCount >= 3 && stats.priceMin !== undefined && stats.priceMax !== undefined) {
    const range =
      stats.priceMin === stats.priceMax
        ? `around ${usd(stats.priceMin)}`
        : `${usd(stats.priceMin)}–${usd(stats.priceMax)}`;
    out.push({
      q: `How much does a ${noun} session cost in ${metro.name}?`,
      a: `Day-pass pricing across ${stats.priceCount} ${metro.name} ${noun} studios ranges ${range}. Individual studios list current rates on their listings.`,
    });
  }

  if (stats.cities.length > 1) {
    const cityList =
      stats.cities.length <= 5
        ? stats.cities.join(", ")
        : stats.cities.slice(0, 5).join(", ") + `, and ${stats.cities.length - 5} more`;
    out.push({
      q: `What cities in the ${metro.name} metro have ${noun} studios?`,
      a: `The ${metro.name} metro's ${noun} studios span ${cityList}.`,
    });
  }

  if (top3.length > 0) {
    const best = top3[0];
    const rating = present(best.google_rating) ? `${best.google_rating}★` : "top-rated";
    const revs = present(best.google_reviews_count)
      ? ` (${best.google_reviews_count} Google reviews)`
      : "";
    out.push({
      q: `What is the highest-rated ${noun} studio in ${metro.name}?`,
      a: `By Google review count, ${best.name} in ${best.city ?? metro.name} is the most-reviewed ${noun} studio on IceSoak's ${where} list: ${rating}${revs}.`,
    });
  }

  return out;
}

function faqPageJsonLd(faqs: { q: string; a: string }[]) {
  if (faqs.length === 0) return undefined;
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqs.map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a },
    })),
  };
}

function uniq<T>(xs: T[]): T[] {
  return Array.from(new Set(xs));
}

// ─── Presentational sub-sections ───────────────────────────────────────────

function CityStatsSection({
  metro,
  noun,
  stats,
}: {
  metro: Metro;
  noun: string;
  stats: CityStatsShape;
}) {
  const topMods = stats.modalityCounts.slice(0, 5);
  return (
    <section className="section city__stats" aria-label={`${metro.name} at a glance`}>
      <h2>{metro.name} {noun} directory at a glance</h2>
      <dl className="detail__facts">
        <div>
          <dt>Verified studios</dt>
          <dd>{stats.studioCount}</dd>
        </div>
        {stats.cities.length > 0 && (
          <div>
            <dt>Cities covered</dt>
            <dd>{stats.cities.slice(0, 6).join(", ")}</dd>
          </div>
        )}
        {topMods.length > 0 && (
          <div>
            <dt>Modalities available</dt>
            <dd>
              {topMods
                .map((m) => `${modalityLabel(m.code)} (${m.count})`)
                .join(", ")}
            </dd>
          </div>
        )}
        {stats.priceCount >= 3 && stats.priceMin !== undefined && stats.priceMax !== undefined && (
          <div>
            <dt>Day-pass range</dt>
            <dd>
              {stats.priceMin === stats.priceMax
                ? `around ${usd(stats.priceMin)}`
                : `${usd(stats.priceMin)}–${usd(stats.priceMax)}`}{" "}
              (across {stats.priceCount} studios with published pricing)
            </dd>
          </div>
        )}
        {stats.ratingAvg !== undefined && (
          <div>
            <dt>Average Google rating</dt>
            <dd>
              {stats.ratingAvg}★ across {stats.ratingCount} rated studios
            </dd>
          </div>
        )}
      </dl>
    </section>
  );
}

function TopStudiosSection({
  metro,
  label,
  studios,
}: {
  metro: Metro;
  label: string;
  studios: Studio[];
}) {
  return (
    <section className="section city__top" aria-label={`Top-reviewed studios in ${metro.name}`}>
      <h2>Top-reviewed {label.toLowerCase()} studios in {metro.name}</h2>
      <p className="muted">
        Ranked by Google review count — a factual signal of local usage, not paid placement.
      </p>
      <ol className="city__top-list">
        {studios.map((s) => (
          <li key={s.id}>
            <a href={`/studio/${s.id}/`}>
              <strong>{s.name}</strong>
            </a>
            {present(s.google_rating) && (
              <>
                {" "}— {s.google_rating}★
                {present(s.google_reviews_count) && ` (${s.google_reviews_count} reviews)`}
              </>
            )}
            {present(s.city) && <div className="muted">{s.city}{present(s.state) && `, ${s.state}`}</div>}
            {present(s.address) && <div className="muted">{s.address}</div>}
          </li>
        ))}
      </ol>
    </section>
  );
}

function CityFaqSection({ faqs }: { faqs: { q: string; a: string }[] }) {
  return (
    <section className="section city__faq" aria-label="Frequently asked questions">
      <h2>Frequently asked questions</h2>
      <dl>
        {faqs.map((f, i) => (
          <div key={i}>
            <dt>{f.q}</dt>
            <dd>{f.a}</dd>
          </div>
        ))}
      </dl>
    </section>
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
