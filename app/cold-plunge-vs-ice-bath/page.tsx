import type { Metadata } from "next";
import Link from "next/link";
import Breadcrumbs from "@/components/Breadcrumbs";
import AnswerCapsule from "@/components/AnswerCapsule";
import JsonLd from "@/components/JsonLd";
import InternalLinks from "@/components/InternalLinks";
import { pageMetadata } from "@/lib/seo";
import { breadcrumbSchema, type Crumb } from "@/lib/jsonld";
import { SITE, abs } from "@/lib/site";

const PATH = "/cold-plunge-vs-ice-bath/";
const UPDATED = "2026-06-25";
const CAPSULE =
  "A cold plunge and an ice bath both use cold-water immersion for recovery. The practical difference is equipment: a cold plunge is a temperature-controlled tub held around 50°F, while an ice bath is manually filled with ice, so its temperature drifts and is harder to control.";

const crumbs: Crumb[] = [
  { name: "Home", path: "/" },
  { name: "Cold plunge vs ice bath", path: PATH },
];

const FAQS = [
  {
    q: "Is a cold plunge colder than an ice bath?",
    a: "Not necessarily. A cold plunge is held at a set temperature, commonly around 50°F. An ice bath can be colder or warmer depending on how much ice is added and how long it sits.",
  },
  {
    q: "Are the benefits of cold plunges and ice baths the same?",
    a: "Yes. Both deliver cold-water immersion, so the physiological effects — reduced soreness, a norepinephrine and alertness boost — are essentially the same. Consistency and temperature matter more than the vessel.",
  },
  {
    q: "Which is better for recovery?",
    a: "For repeatable recovery, a temperature-controlled cold plunge is easier to dose consistently. An ice bath works fine but is harder to keep at a stable temperature.",
  },
];

export const metadata: Metadata = pageMetadata({
  title: "Cold Plunge vs Ice Bath",
  description:
    "Cold plunge vs ice bath: the difference is temperature control, not the benefits. Both use cold-water immersion around 50°F for recovery.",
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
    headline: "Cold Plunge vs Ice Bath",
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
        <h1>Cold Plunge vs Ice Bath</h1>
        <p className="byline">By {SITE.editor} · Last updated June 25, 2026</p>
        <AnswerCapsule text={CAPSULE} />

        <h2>The core difference: temperature control</h2>
        <p>
          A cold plunge is a purpose-built tub with a chiller that holds a set
          temperature, typically 45–55°F. An ice bath is any tub filled with
          water and ice by hand. Because the ice melts, an ice bath&apos;s
          temperature changes during the session and varies from one fill to the
          next, which makes consistent dosing harder.
        </p>

        <h2>Benefits are effectively the same</h2>
        <p>
          Both methods are cold-water immersion, so the physiological response is
          the same: vasoconstriction, a rise in norepinephrine, and reduced
          delayed-onset muscle soreness after exercise. The vessel does not change
          the underlying effect — temperature and time do.
        </p>

        <h2>Which should you choose?</h2>
        <p>
          If you want repeatable sessions and minimal setup, a temperature-
          controlled cold plunge is more convenient. If you are improvising at
          home or after an event, an ice bath achieves the same exposure for the
          cost of ice. Either way, the safe ranges for temperature and duration
          are identical.
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
          <Link href="/guides/is-a-40-degree-ice-bath-safe/">
            is a 40°F ice bath safe
          </Link>{" "}
          and{" "}
          <Link href="/guides/how-long-should-you-stay-in-a-cold-plunge/">
            how long you should stay in a cold plunge
          </Link>
          .
        </p>
      </article>

      <InternalLinks type="guide" slug="cold-plunge-vs-ice-bath" />
    </div>
  );
}
