import type { Metadata } from "next";
import Link from "next/link";
import Breadcrumbs from "@/components/Breadcrumbs";
import AnswerCapsule from "@/components/AnswerCapsule";
import JsonLd from "@/components/JsonLd";
import { pageMetadata } from "@/lib/seo";
import { breadcrumbSchema, type Crumb } from "@/lib/jsonld";
import { SITE, abs } from "@/lib/site";

const PATH = "/infrared-vs-traditional-sauna/";
const UPDATED = "2026-06-25";
const CAPSULE =
  "Traditional saunas heat the air to 150–195°F, while infrared saunas heat the body directly at a milder 110–135°F. Infrared feels gentler and suits longer 20–45 minute sessions; traditional saunas deliver higher heat, steam options, and a more intense sweat in less time.";

const crumbs: Crumb[] = [
  { name: "Home", path: "/" },
  { name: "Infrared vs traditional sauna", path: PATH },
];

const FAQS = [
  {
    q: "Is an infrared sauna hotter than a traditional sauna?",
    a: "No. Infrared saunas run cooler air, about 110–135°F, versus 150–195°F for traditional saunas. Infrared heats the body directly, so it still produces a deep sweat at a lower air temperature.",
  },
  {
    q: "Which sauna is better for beginners?",
    a: "Many beginners find infrared more comfortable because the lower air temperature is easier to tolerate for longer sessions. Traditional saunas are more intense but shorter.",
  },
  {
    q: "Do both types offer the same benefits?",
    a: "Both provide heat exposure, sweating, and a cardiovascular response associated with relaxation and recovery. Traditional saunas reach higher temperatures; infrared achieves similar sweat over a longer, milder session.",
  },
];

export const metadata: Metadata = pageMetadata({
  title: "Infrared vs Traditional Sauna",
  description:
    "Infrared vs traditional sauna: infrared runs 110–135°F and heats the body directly; traditional saunas reach 150–195°F. Compare heat, session length, and feel.",
  path: PATH,
  index: true,
});

export default function Page() {
  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: FAQS.map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a },
    })),
  };
  const articleSchema = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "Infrared vs Traditional Sauna",
    description: CAPSULE,
    datePublished: UPDATED,
    dateModified: UPDATED,
    author: { "@type": "Organization", name: SITE.editor },
    publisher: { "@id": abs("/#organization") },
    mainEntityOfPage: abs(PATH),
  };

  return (
    <div className="wrap">
      <JsonLd data={[breadcrumbSchema(crumbs), faqSchema, articleSchema]} />
      <Breadcrumbs crumbs={crumbs} />
      <article className="prose">
        <h1>Infrared vs Traditional Sauna</h1>
        <p className="byline">By {SITE.editor} · Last updated June 25, 2026</p>
        <AnswerCapsule text={CAPSULE} />

        <h2>How they heat you</h2>
        <p>
          A traditional sauna warms the air, usually to 150–195°F, and you heat up
          from that hot environment. An infrared sauna uses infrared panels to
          warm your body directly while the air stays cooler, around 110–135°F.
          The result is a deep sweat at a lower ambient temperature.
        </p>

        <h2>Session length and feel</h2>
        <p>
          Because infrared air is milder, sessions often run 20–45 minutes and
          feel less harsh. Traditional saunas are more intense and typically last
          10–20 minutes, with the option of adding steam by pouring water on hot
          rocks.
        </p>

        <h2>Choosing between them</h2>
        <p>
          Pick infrared if you prefer a longer, gentler session or find high heat
          uncomfortable. Pick traditional if you want maximum heat, steam, and a
          faster sweat. Both are associated with relaxation and recovery; the
          difference is intensity and duration, not whether one &quot;works.&quot;
        </p>

        <section className="faq">
          <h2>Frequently asked questions</h2>
          {FAQS.map((f) => (
            <details key={f.q}>
              <summary>{f.q}</summary>
              <p>{f.a}</p>
            </details>
          ))}
        </section>

        <p>
          Related reading:{" "}
          <Link href="/guides/how-hot-is-an-infrared-sauna/">
            how hot is an infrared sauna
          </Link>{" "}
          and <Link href="/guides/sauna-benefits/">sauna benefits</Link>.
        </p>
      </article>
    </div>
  );
}
