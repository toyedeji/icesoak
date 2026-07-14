import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import Breadcrumbs from "@/components/Breadcrumbs";
import AnswerCapsule from "@/components/AnswerCapsule";
import AffiliateSection from "@/components/AffiliateSection";
import InternalLinks from "@/components/InternalLinks";
import JsonLd from "@/components/JsonLd";
import { QUESTIONS, questionBySlug } from "@/lib/data";
import { GUIDE_FAQS } from "@/lib/guideFAQs";
import { pageMetadata, clamp } from "@/lib/seo";
import { articleSchema, faqSchema, breadcrumbSchema, type Crumb } from "@/lib/jsonld";
import { formatDate } from "@/lib/format";

type P = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return QUESTIONS.map((q) => ({ slug: q.slug }));
}

export async function generateMetadata({ params }: P): Promise<Metadata> {
  const q = questionBySlug((await params).slug);
  if (!q) return {};
  return pageMetadata({
    title: q.question,
    description: clamp(q.capsule ?? ""),
    path: `/guides/${q.slug}/`,
    index: true,
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
        <p className="byline">
          By {q.author}
          {updated ? ` · Last updated ${updated}` : ""}
        </p>
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

      <AffiliateSection type="general" />
    </div>
  );
}
