import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Breadcrumbs from "@/components/Breadcrumbs";
import JsonLd from "@/components/JsonLd";
import LazyMap from "@/components/LazyMap";
import { STUDIOS, studioById, metroByKey } from "@/lib/data";
import { studioSchema, breadcrumbSchema, type Crumb } from "@/lib/jsonld";
import { pageMetadata, clamp } from "@/lib/seo";
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

  return (
    <div className="wrap">
      <JsonLd data={[breadcrumbSchema(crumbs), studioSchema(s)]} />
      <Breadcrumbs crumbs={crumbs} />
      <h1>{s.name}</h1>
      {loc && <p className="lead">{loc}</p>}

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

      <p>
        {present(s.website) && (
          <a className="btn" href={s.website as string} rel="nofollow noopener" target="_blank">
            Visit website
          </a>
        )}{" "}
        {present(s.booking_url) && (
          <a
            className="btn"
            href={s.booking_url as string}
            rel="nofollow noopener"
            target="_blank"
          >
            Book a session
          </a>
        )}
      </p>

      <div className="section">
        <LazyMap studios={[s]} center={mapCenter} zoom={present(s.lat) ? 14 : 11} />
      </div>

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
    </div>
  );
}
