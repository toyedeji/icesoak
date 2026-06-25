import Link from "next/link";
import type { Studio } from "@/lib/types";
import { val, usd, tempRange, listModalities, formatDate, present } from "@/lib/format";

// Renders a studio summary. Every optional field is guarded — nothing prints
// "null"; absent data is simply omitted.
export default function StudioCard({ studio }: { studio: Studio }) {
  const modalities = listModalities(studio.modalities);
  const dayPass = usd(studio.day_pass_price_usd);
  const member = usd(studio.membership_from_usd);
  const temps = tempRange(studio.plunge_temp_f_min, studio.plunge_temp_f_max);
  const locality = [val(studio.neighborhood), val(studio.city), val(studio.state)]
    .filter(Boolean)
    .join(", ");
  const verified = formatDate(studio.last_verified);

  return (
    <article className="card">
      <h3 className="card__title">
        <Link href={`/studio/${studio.id}/`}>{studio.name}</Link>
      </h3>
      {locality && <p className="card__meta">{locality}</p>}
      {modalities && <p className="card__modalities">{modalities}</p>}
      <dl className="card__facts">
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
        {present(studio.google_rating) && (
          <div>
            <dt>Rating</dt>
            <dd>
              {studio.google_rating}
              {present(studio.google_reviews_count)
                ? ` (${studio.google_reviews_count})`
                : ""}
            </dd>
          </div>
        )}
      </dl>
      {verified ? (
        <p className="card__verified">Last verified {verified}</p>
      ) : (
        <p className="card__verified card__verified--pending">Verification pending</p>
      )}
    </article>
  );
}
