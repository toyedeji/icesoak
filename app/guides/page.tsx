import type { Metadata } from "next";
import Link from "next/link";
import Breadcrumbs from "@/components/Breadcrumbs";
import JsonLd from "@/components/JsonLd";
import { QUESTIONS } from "@/lib/data";
import { pageMetadata } from "@/lib/seo";
import { breadcrumbSchema, type Crumb } from "@/lib/jsonld";
import { abs } from "@/lib/site";
import { modalityLabel } from "@/lib/format";

const crumbs: Crumb[] = [
  { name: "Home", path: "/" },
  { name: "Guides", path: "/guides/" },
];

export const metadata: Metadata = pageMetadata({
  title: "Cold Plunge & Sauna Guides",
  description:
    "Factual, source-led guides to cold plunge and sauna use: temperatures, timing, safety, benefits, and contrast therapy. No hype, just numbers.",
  path: "/guides/",
  index: true,
});

export default function GuidesIndex() {
  const categories = Array.from(new Set(QUESTIONS.map((q) => q.category)));
  const listSchema = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: "IceSoak guides",
    numberOfItems: QUESTIONS.length,
    itemListElement: QUESTIONS.map((q, i) => ({
      "@type": "ListItem",
      position: i + 1,
      url: abs(`/guides/${q.slug}/`),
      name: q.question,
    })),
  };

  return (
    <div className="wrap">
      <JsonLd data={[breadcrumbSchema(crumbs), listSchema]} />
      <Breadcrumbs crumbs={crumbs} />
      <h1>Cold Plunge &amp; Sauna Guides</h1>
      <p className="lead">
        Plain-language answers to the most common cold plunge, sauna, and
        contrast-therapy questions — led by real temperatures, durations, and
        evidence.
      </p>

      {categories.map((cat) => {
        const items = QUESTIONS.filter((q) => q.category === cat);
        return (
          <section key={cat} className="section">
            <h2>{modalityLabel(cat) === cat ? labelFor(cat) : modalityLabel(cat)}</h2>
            <ul className="linklist">
              {items.map((q) => (
                <li key={q.slug}>
                  <Link href={`/guides/${q.slug}/`}>{q.question}</Link>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}

function labelFor(cat: string): string {
  const map: Record<string, string> = {
    "cold-plunge": "Cold plunge",
    sauna: "Sauna",
    "contrast-therapy": "Contrast therapy",
    comparison: "Comparisons",
  };
  return map[cat] ?? cat;
}
