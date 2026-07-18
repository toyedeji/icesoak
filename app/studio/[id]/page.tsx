import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Breadcrumbs from "@/components/Breadcrumbs";
import JsonLd from "@/components/JsonLd";
import LazyMap from "@/components/LazyMap";
import { STUDIOS, studioById, metroByKey } from "@/lib/data";
import { studioSchema, breadcrumbSchema, type Crumb } from "@/lib/jsonld";
import { pageMetadata, clamp } from "@/lib/seo";
import type { Studio } from "@/lib/types";
import {
  val,
  usd,
  tempRange,
  modalityLabel,
  listModalities,
  formatDate,
  present,
} from "@/lib/format";

type P = { params: Promise<{ id: string }> };

// Enum → human phrasing for the two fields that ship as machine codes.
const SESSION_LABELS: Record<string, string> = {
  free_flow: "free-flow",
  guided_social: "guided social",
};
const ACCESS_LABELS: Record<string, string> = {
  both: "day-pass and membership",
  membership_only: "membership-only",
  day_pass: "day-pass",
};

function humanize(map: Record<string, string>, code: string): string {
  return map[code] ?? code.replace(/_/g, " ");
}

// Haversine great-circle distance in miles.
function milesBetween(
  a: { lat: number; lng: number },
  b: { lat: number; lng: number },
): number {
  const R = 3958.8;
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const s1 = Math.sin(dLat / 2);
  const s2 = Math.sin(dLng / 2);
  const h = s1 * s1 + Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * s2 * s2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}

function nearbyStudios(current: Studio, n = 4): Studio[] {
  const sameMetro = STUDIOS.filter((x) => x.id !== current.id && x.metro === current.metro);
  if (!present(current.lat) || !present(current.lng)) {
    return sameMetro.slice(0, n);
  }
  const origin = { lat: current.lat as number, lng: current.lng as number };
  return sameMetro
    .filter((x) => present(x.lat) && present(x.lng))
    .map((x) => ({
      studio: x,
      d: milesBetween(origin, { lat: x.lat as number, lng: x.lng as number }),
    }))
    .sort((a, b) => a.d - b.d)
    .slice(0, n)
    .map((r) => r.studio);
}

// Only render an FAQ item when its source field is populated.
function buildFaqs(s: Studio): { q: string; a: string }[] {
  const out: { q: string; a: string }[] = [];

  const modList = listModalities(s.modalities);
  if (modList) {
    out.push({
      q: `What modalities does ${s.name} offer?`,
      a: `${s.name} offers ${modList}.`,
    });
  }

  const dayPass = usd(s.day_pass_price_usd);
  const member = usd(s.membership_from_usd);
  if (dayPass || member) {
    const parts: string[] = [];
    if (dayPass) parts.push(`day passes start at ${dayPass}`);
    if (member) parts.push(`memberships from ${member}/mo`);
    out.push({
      q: `How much does a day pass cost at ${s.name}?`,
      a: `At ${s.name}, ${parts.join("; ")}.`,
    });
  }

  const temps = tempRange(s.plunge_temp_f_min, s.plunge_temp_f_max);
  if (temps) {
    out.push({
      q: `How cold is the plunge at ${s.name}?`,
      a: `The cold plunge at ${s.name} runs ${temps}.`,
    });
  }

  const locBits = [val(s.address), val(s.neighborhood), val(s.city)].filter(Boolean);
  if (locBits.length > 0) {
    const stateSuffix = present(s.state) ? `, ${s.state}` : "";
    out.push({
      q: `Where is ${s.name} located?`,
      a: `${s.name} is located at ${locBits.join(", ")}${stateSuffix}.`,
    });
  }

  if (present(s.booking_url)) {
    out.push({
      q: `How do I book a session at ${s.name}?`,
      a: `Book directly through ${s.name}'s booking page linked above.`,
    });
  }

  return out;
}

function faqPageSchema(faqs: { q: string; a: string }[]) {
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

export function generateStaticParams() {
  return STUDIOS.map((s) => ({ id: s.id }));
}

export async function generateMetadata({ params }: P): Promise<Metadata> {
  const s = studioById((await params).id);
  if (!s) return {};
  const loc = [val(s.city), val(s.state)].filter(Boolean).join(", ");
  const mod = listModalities(s.modalities);
  const desc = `${s.name}${loc ? ` in ${loc}` : ""}.${mod ? ` Modalities: ${mod}.` : ""} Verified studio listing on IceSoak with location and details.`;
  return pageMetadata({
    title: `${s.name}${loc ? ` — ${loc}` : ""}`,
    description: clamp(desc),
    path: `/studio/${s.id}/`,
    index: true,
  });
}

export default async function Page({ params }: P) {
  const s = studioById((await params).id);
  if (!s) notFound();

  const metro = metroByKey(s.metro);
  const loc = [val(s.neighborhood), val(s.city), val(s.state)].filter(Boolean).join(", ");
  const verified = formatDate(s.last_verified);
  const temps = tempRange(s.plunge_temp_f_min, s.plunge_temp_f_max);
  const dayPass = usd(s.day_pass_price_usd);
  const member = usd(s.membership_from_usd);
  const modalities = Array.isArray(s.modalities) ? s.modalities : [];

  const crumbs: Crumb[] = [
    { name: "Home", path: "/" },
    ...(metro
      ? [{ name: `${metro.name}, ${metro.state}`, path: `/cold-plunge/${metro.slug}/` }]
      : []),
    { name: s.name, path: `/studio/${s.id}/` },
  ];

  const mapCenter =
    present(s.lat) && present(s.lng)
      ? { lat: s.lat as number, lng: s.lng as number }
      : metro
        ? { lat: metro.lat, lng: metro.lng }
        : { lat: 39.5, lng: -98.35 };

  // BLUF answer capsule for the studio, built only from present facts.
  const capsuleParts = [
    `${s.name} is a ${listModalities(s.modalities) || "recovery"} studio${loc ? ` in ${loc}` : ""}.`,
  ];
  if (temps) capsuleParts.push(`Cold plunge runs ${temps}.`);
  if (dayPass) capsuleParts.push(`Day passes start at ${dayPass}.`);
  if (verified) capsuleParts.push(`Details last verified ${verified}.`);

  const faqs = buildFaqs(s);
  const faqBlock = faqPageSchema(faqs);
  const nearby = nearbyStudios(s);
  const sessionProse =
    present(s.session_style) && present(s.access)
      ? `${s.name} offers ${humanize(SESSION_LABELS, s.session_style as string)} sessions with ${humanize(ACCESS_LABELS, s.access as string)} access.`
      : undefined;

  return (
    <div className="wrap">
      <JsonLd data={[breadcrumbSchema(crumbs), studioSchema(s), faqBlock].filter(Boolean)} />
      <Breadcrumbs crumbs={crumbs} />
      <h1>{s.name}</h1>
      {loc && <p className="lead">{loc}</p>}
      {present(s.address) && (
        <address className="studio__address">{s.address}</address>
      )}

      <div className="capsule" role="note">
        <p className="capsule__label">At a glance</p>
        <p className="capsule__text">{capsuleParts.join(" ")}</p>
      </div>

      {modalities.length > 0 && (
        <p>
          {modalities.map((m) => (
            <span key={m} className="pill">
              {modalityLabel(m)}
            </span>
          ))}
        </p>
      )}

      {sessionProse && <p>{sessionProse}</p>}

      <dl className="detail__facts">
        {present(s.brand) && (
          <div>
            <dt>Brand</dt>
            <dd>{s.brand}</dd>
          </div>
        )}
        {temps && (
          <div>
            <dt>Plunge temp</dt>
            <dd>{temps}</dd>
          </div>
        )}
        {dayPass && (
          <div>
            <dt>Day pass</dt>
            <dd>from {dayPass}</dd>
          </div>
        )}
        {member && (
          <div>
            <dt>Membership</dt>
            <dd>from {member}/mo</dd>
          </div>
        )}
        {present(s.format) && (
          <div>
            <dt>Format</dt>
            <dd>{(s.format as string).replace(/_/g, " ")}</dd>
          </div>
        )}
        {present(s.google_rating) && (
          <div>
            <dt>Google rating</dt>
            <dd>
              {s.google_rating}
              {present(s.google_reviews_count) ? ` (${s.google_reviews_count} reviews)` : ""}
            </dd>
          </div>
        )}
      </dl>

      <div className="detail__cta">
        {present(s.website) && (
          <a className="btn" href={s.website as string} rel="nofollow noopener" target="_blank">
            Visit website
          </a>
        )}
        {present(s.booking_url) && (
          <a
            className="btn"
            href={s.booking_url as string}
            rel="nofollow noopener"
            target="_blank"
          >
            Book a session →
          </a>
        )}
      </div>

      <div className="section">
        <LazyMap studios={[s]} center={mapCenter} zoom={present(s.lat) ? 14 : 11} />
      </div>

      {faqs.length > 0 && (
        <section className="studio__faq" aria-label="Frequently asked questions">
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
      )}

      <p>
        <span className="verified-badge">
          {verified ? `✓ Last verified ${verified}` : "⏱ Verification pending"}
        </span>
        {present(s.source_urls) && (
          <span className="muted"> · Source: studio website.</span>
        )}
      </p>

      {metro && (
        <p>
          <a href={`/cold-plunge/${metro.slug}/`}>
            ← More studios in {metro.name}, {metro.state}
          </a>
        </p>
      )}

      {nearby.length > 0 && metro && (
        <section className="studio__nearby" aria-label="Nearby studios">
          <h2>More cold plunge studios in {metro.name}</h2>
          <ul>
            {nearby.map((n) => (
              <li key={n.id}>
                <a href={`/studio/${n.id}/`}>{n.name}</a>
                {present(n.city) && ` — ${n.city}`}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
