import type { Metadata } from "next";
import Link from "next/link";
import Breadcrumbs from "@/components/Breadcrumbs";
import JsonLd from "@/components/JsonLd";
import { pageMetadata } from "@/lib/seo";
import { breadcrumbSchema, type Crumb } from "@/lib/jsonld";
import { SITE } from "@/lib/site";

const PATH = "/editorial-standards/";

const crumbs: Crumb[] = [
  { name: "Home", path: "/" },
  { name: "Editorial standards", path: PATH },
];

export const metadata: Metadata = pageMetadata({
  title: "Editorial Standards",
  description:
    "How IceSoak guides are written: compiled from published sources, not clinical advice, and not reviewed by a clinician. What that means for you, and how to send a correction.",
  path: PATH,
  index: true,
});

export default function EditorialStandardsPage() {
  return (
    <div className="wrap">
      <JsonLd data={[breadcrumbSchema(crumbs)]} />
      <Breadcrumbs crumbs={crumbs} />
      <article className="prose">
        <h1>Editorial standards</h1>
        <p className="lead">
          Every guide on this site links here from its byline. This page says
          plainly what those guides are and what they are not.
        </p>

        <section>
          <h2>Who writes these guides</h2>
          <p>
            {SITE.name} is a directory. The guides are compiled from published
            sources by the same small operation that maintains the studio
            listings. Until August 2026 they carried the byline &ldquo;By
            IceSoak Editorial.&rdquo; There is no editorial department, and that
            byline has been replaced with one that says what is true:
            &ldquo;Compiled by IceSoak.&rdquo;
          </p>
        </section>

        <section>
          <h2>They are not medically reviewed</h2>
          <p>
            No clinician reviews this material before or after publication. No
            author on this site holds a medical qualification, and none is
            claimed. Where a guide describes a physiological effect, a
            temperature, or a duration, treat it as a summary of what is
            commonly published on the subject — not as a clinical recommendation
            and not as a substitute for advice from someone who knows your
            history.
          </p>
          <p>
            Cold and heat exposure carry real risks that vary by individual.
            Cardiovascular disease, uncontrolled hypertension, Raynaud&apos;s,
            cold intolerance, thyroid conditions, pregnancy, and many
            prescription medications all change the calculation. If any of those
            apply to you, ask your doctor before starting or changing a
            practice.
          </p>
        </section>

        <section>
          <h2>How claims are handled</h2>
          <p>
            Guides describe what is commonly reported about cold and heat
            exposure. They do not cite studies, and as of August 2026 phrasing
            that appealed to unnamed research — &ldquo;studies show,&rdquo;
            &ldquo;research has found&rdquo; — has been removed rather than
            given sources after the fact. An unverified citation borrows
            confidence nobody has actually earned, so where a claim could not
            stand as plain description it was cut instead.
          </p>
          <p>
            Guides that deal with a specific medical condition, or with a
            temperature or duration where the wrong number matters, carry a
            disclaimer at the top and do not carry product links. That
            suppression is enforced at build time, not by convention.
          </p>
        </section>

        <section>
          <h2>Affiliate links</h2>
          <p>
            Some pages link to products on Amazon and earn a commission on
            purchases, at no extra cost to you. Those blocks are labelled where
            they appear. They are switched off entirely on guides about health
            conditions and on guides about safety limits — selling a cold plunge
            tub at the bottom of a page about autoimmune disease, or at the
            bottom of a page explaining when cold water is dangerous, is not a
            trade we are willing to make. Studio listings are never paid
            placements.
          </p>
        </section>

        <section>
          <h2>Corrections</h2>
          <p>
            If something here is wrong, tell us and it gets fixed or removed.
            Send corrections to{" "}
            <a href={`mailto:${SITE.corrections}`}>{SITE.corrections}</a>. Point
            at the page and the sentence; that is enough.
          </p>
          <p>
            The date on each guide is the last time its text actually changed,
            not a rolling freshness stamp.
          </p>
        </section>

        <p>
          <Link href="/guides/">Back to the guides</Link>
        </p>
      </article>
    </div>
  );
}
