import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import Breadcrumbs from "@/components/Breadcrumbs";
import AnswerCapsule from "@/components/AnswerCapsule";
import AffiliateSection from "@/components/AffiliateSection";
import MedicalDisclaimer from "@/components/MedicalDisclaimer";
import InternalLinks from "@/components/InternalLinks";
import JsonLd from "@/components/JsonLd";
import { QUESTIONS, questionBySlug, hasGuideBody, isDeniedGuide } from "@/lib/data";
import { showsAffiliate, showsDisclaimer } from "@/lib/riskTier";
import { GUIDE_FAQS } from "@/lib/guideFAQs";
import { pageMetadata, clamp } from "@/lib/seo";
import { articleSchema, faqSchema, breadcrumbSchema, type Crumb } from "@/lib/jsonld";
import { formatDate } from "@/lib/format";
import { SITE } from "@/lib/site";

type P = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  // The isDeniedGuide() filter is redundant with the one in lib/data.ts and is
  // kept deliberately. This is the exact line that decides whether a removed
  // guide gets a static file written for it, and an existing file shadows the
  // force = false 301 in netlify.toml. Cheap insurance at the one place it
  // matters. See guide_denylist.json.
  return QUESTIONS.filter((q) => !isDeniedGuide(q.slug)).map((q) => ({ slug: q.slug }));
}

export async function generateMetadata({ params }: P): Promise<Metadata> {
  const q = questionBySlug((await params).slug);
  if (!q) return {};
  // A guide with no body is served noindex,follow: the URL and its internal
  // links stay alive, but Google drops it from the index instead of holding it
  // as thin content. scripts/postexport.mjs reads the rendered robots tag, so
  // this also removes the page from the sitemap automatically. Writing a body
  // flips it back to indexable with no code change.
  const published = hasGuideBody(q);
  return pageMetadata({
    title: q.question,
    description: clamp(q.capsule ?? ""),
    path: `/guides/${q.slug}/`,
    index: published,
  });
}

export default async function Page({ params }: P) {
  const base = questionBySlug((await params).slug);
  if (!base) notFound();

  // Merge any curated supplemental FAQs into the guide's own list. This enriches
  // both the visible FAQ section and the FAQPage JSON-LD (faqSchema reads .faqs).
  const extraFaqs = GUIDE_FAQS[base.slug] ?? [];
  const q = extraFaqs.length
    ? { ...base, faqs: [...(base.faqs ?? []), ...extraFaqs] }
    : base;

  const path = `/guides/${q.slug}/`;
  const crumbs: Crumb[] = [
    { name: "Home", path: "/" },
    { name: "Guides", path: "/guides/" },
    { name: q.question, path },
  ];
  const updated = formatDate(q.updated);

  // Related guides in the same category for the internal-link silo.
  const related = QUESTIONS.filter(
    (x) => x.category === q.category && x.slug !== q.slug,
  ).slice(0, 4);

  return (
    <div className="wrap">
      <JsonLd data={[breadcrumbSchema(crumbs), articleSchema(q, path), faqSchema(q)]} />
      <Breadcrumbs crumbs={crumbs} />
      <article className="prose">
        <h1>{q.question}</h1>
        {/*
          Was "By IceSoak Editorial · Last updated July 6, 2026" on all 32
          guides. There is no editorial body and no medical reviewer, and the
          uniform date was an artifact of bulk generation rather than a real
          revision. Both halves now say what is actually true, and the
          not-reviewed claim links to the page that explains it.
        */}
        <p className="byline">
          Compiled by {q.author || SITE.editor} ·{" "}
          <Link href="/editorial-standards/">Not medically reviewed</Link>
          {updated ? ` · Last updated ${updated}` : ""}
        </p>
        {showsDisclaimer(q.risk_tier) && <MedicalDisclaimer tier={q.risk_tier!} />}
        <AnswerCapsule text={q.capsule} />

        {(q.sections ?? []).map((sec) => (
          <section key={sec.h2}>
            <h2>{sec.h2}</h2>
            <p>{sec.body}</p>
          </section>
        ))}

        {q.faqs && q.faqs.length > 0 && (
          <section className="faq">
            <h2>Frequently asked questions</h2>
            {q.faqs.map((f) => (
              <details key={f.q}>
                <summary>{f.q}</summary>
                <p>{f.a}</p>
              </details>
            ))}
          </section>
        )}
      </article>

      {related.length > 0 && (
        <section className="section">
          <h2>Related guides</h2>
          <ul className="linklist">
            {related.map((r) => (
              <li key={r.slug}>
                <Link href={`/guides/${r.slug}/`}>{r.question}</Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      <InternalLinks type="guide" slug={q.slug} />

      {showsAffiliate(q.risk_tier) && <AffiliateSection type="general" />}
    </div>
  );
}
