import Link from "next/link";
import { QUESTIONS, metroBySlug } from "@/lib/data";
import { studiosForVertical, type Vertical } from "@/lib/studios";
import {
  GUIDE_TO_CITIES,
  CITY_TO_GUIDES,
  TOP_LEVEL_GUIDES,
  SAUNA_GUIDES,
} from "@/lib/internalLinks";

type LinkItem = { href: string; label: string };

// Resolve a guide slug to a real, existing URL + descriptive anchor text.
// Returns null for anything not backed by real content so we never emit a
// broken internal link.
function resolveGuide(slug: string): LinkItem | null {
  const q = QUESTIONS.find((x) => x.slug === slug);
  if (q) return { href: `/guides/${q.slug}/`, label: `${q.question} →` };
  const topTitle = TOP_LEVEL_GUIDES[slug];
  if (topTitle) return { href: `/${slug}/`, label: `${topTitle} →` };
  return null;
}

// Resolve a metro slug to an existing directory page for a guide's vertical.
// Prefers sauna pages for sauna guides, falls back to cold-plunge, and skips
// the metro entirely when it has no directory page at all (e.g. metros with no
// modality-tagged studios).
function resolveCityForGuide(citySlug: string, guideSlug: string): LinkItem | null {
  const metro = metroBySlug(citySlug);
  if (!metro) return null;
  const order: Vertical[] = SAUNA_GUIDES.has(guideSlug)
    ? ["sauna", "cold-plunge"]
    : ["cold-plunge", "sauna"];
  for (const v of order) {
    if (studiosForVertical(metro, v).length > 0) {
      const noun = v === "sauna" ? "Sauna" : "Cold plunge";
      return { href: `/${v}/${metro.slug}/`, label: `${noun} studios in ${metro.name} →` };
    }
  }
  return null;
}

function dedupe(items: LinkItem[]): LinkItem[] {
  const seen = new Set<string>();
  return items.filter((it) => (seen.has(it.href) ? false : (seen.add(it.href), true)));
}

// Guide pages get a "Find studios near you" block of city links; city pages get
// a "Learn more" block of guide links. Renders nothing when nothing resolves.
export default function InternalLinks({
  type,
  slug,
}: {
  type: "guide" | "city";
  slug: string;
}) {
  if (type === "guide") {
    const items = dedupe(
      (GUIDE_TO_CITIES[slug] ?? [])
        .map((c) => resolveCityForGuide(c, slug))
        .filter((x): x is LinkItem => x !== null),
    );
    if (items.length === 0) return null;
    return (
      <section className="section">
        <h2>Find studios near you</h2>
        <ul className="linklist">
          {items.map((it) => (
            <li key={it.href}>
              <Link href={it.href}>{it.label}</Link>
            </li>
          ))}
        </ul>
      </section>
    );
  }

  const items = dedupe(
    (CITY_TO_GUIDES[slug] ?? [])
      .map(resolveGuide)
      .filter((x): x is LinkItem => x !== null),
  );
  if (items.length === 0) return null;
  return (
    <section className="section">
      <h2>Learn more</h2>
      <ul className="linklist">
        {items.map((it) => (
          <li key={it.href}>
            <Link href={it.href}>{it.label}</Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
