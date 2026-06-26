import Link from "next/link";
import { METROS, QUESTIONS, STUDIOS } from "@/lib/data";

// Homepage / directory hub. Fully static, internally links the city <-> studio
// <-> guide silo so crawlers and AI engines can traverse the whole site.
export default function Home() {
  const featuredGuides = QUESTIONS.slice(0, 6);
  const studioCount = STUDIOS.length;

  return (
    <>
      <section className="hero">
        <div className="wrap">
          <h1>Find verified cold plunge, sauna &amp; contrast-therapy studios</h1>
          <p className="lead">
            IceSoak is a factual directory of {studioCount} recovery studios across{" "}
            {METROS.length} metros — with modalities, maps, and a last-verified
            date on every listing. No hype, just the numbers you need to choose.
          </p>
          <div className="cta-row">
            <Link className="btn" href="/cold-plunge/denver/">
              Browse cold plunge
            </Link>
            <Link className="btn btn--ghost" href="/guides/">
              Read the guides
            </Link>
          </div>
        </div>
      </section>

      <div className="wrap">
        <section className="section">
          <h2>Browse by metro</h2>
          <div className="tiles">
            {METROS.map((m) => {
              const count = STUDIOS.filter((s) => s.metro === m.metro).length;
              return (
                <Link key={m.slug} className="tile" href={`/cold-plunge/${m.slug}/`}>
                  <strong>
                    {m.name}, {m.state}
                  </strong>
                  <span>
                    {count} {count === 1 ? "studio" : "studios"} · {m.blurb}
                  </span>
                </Link>
              );
            })}
          </div>
        </section>

        <section className="section">
          <h2>Browse by modality</h2>
          <div className="tiles">
            <ModalityTile
              href="/cold-plunge/denver/"
              title="Cold plunge"
              sub="Cold-water immersion around 50°F"
            />
            <ModalityTile
              href="/sauna/dallas-fort-worth/"
              title="Sauna"
              sub="Traditional and infrared heat"
            />
            <ModalityTile
              href="/infrared-sauna/dallas-fort-worth/"
              title="Infrared sauna"
              sub="Direct-heat sessions, 110–135°F"
            />
            <ModalityTile
              href="/contrast-therapy/denver/"
              title="Contrast therapy"
              sub="Alternating heat and cold"
            />
          </div>
        </section>

        <section className="section">
          <h2>Popular guides</h2>
          <ul className="linklist">
            {featuredGuides.map((q) => (
              <li key={q.slug}>
                <Link href={`/guides/${q.slug}/`}>{q.question}</Link>
              </li>
            ))}
          </ul>
          <p>
            <Link href="/guides/">All guides →</Link>
          </p>
        </section>

        <section className="section">
          <h2>Compare</h2>
          <div className="tiles">
            <Link className="tile" href="/cold-plunge-vs-ice-bath/">
              <strong>Cold plunge vs ice bath</strong>
              <span>Temperature control, not different benefits</span>
            </Link>
            <Link className="tile" href="/infrared-vs-traditional-sauna/">
              <strong>Infrared vs traditional sauna</strong>
              <span>110–135°F vs 150–195°F</span>
            </Link>
          </div>
        </section>
      </div>
    </>
  );
}

function ModalityTile({ href, title, sub }: { href: string; title: string; sub: string }) {
  return (
    <Link className="tile" href={href}>
      <strong>{title}</strong>
      <span>{sub}</span>
    </Link>
  );
}
