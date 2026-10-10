import { AFFILIATE_PRODUCTS, type AffiliateProduct } from "@/lib/affiliates";

type SectionType = "cold_plunge" | "sauna" | "general";

/**
 * The visible button text for a product.
 *
 * Half the products in AFFILIATE_PRODUCTS link to amazon.com; the rest point
 * straight at the merchant (Plunge via Impact.com, Sweaty Yeti direct). Every
 * button used to say "View on Amazon →" regardless, which was both a lie on
 * the merchant-direct rows and a wasted trust signal: a shopper who recognises
 * the Plunge brand is more likely to click a "View at Plunge" button than
 * one that mis-labels itself as Amazon.
 */
function ctaLabelFor(url: string, brand: string): string {
  try {
    const host = new URL(url).hostname.toLowerCase();
    if (host.includes("amazon.")) return "View on Amazon →";
    if (host.includes("plunge.")) return "View at Plunge →";
    if (host.includes("sweatyyeti")) return "View at Sweaty Yeti →";
    if (host.includes("icebarrel")) return "View at Ice Barrel →";
    return `View at ${brand} →`;
  } catch {
    return `View at ${brand} →`;
  }
}

function productsForType(type: SectionType): AffiliateProduct[] {
  if (type === "cold_plunge") {
    return AFFILIATE_PRODUCTS.filter(
      (p) => p.category === "cold_plunge" || p.category === "accessories",
    );
  }
  if (type === "sauna") {
    return AFFILIATE_PRODUCTS.filter(
      (p) => p.category === "sauna" || p.category === "accessories",
    );
  }
  return [
    ...AFFILIATE_PRODUCTS.filter((p) => p.category === "cold_plunge").slice(0, 2),
    ...AFFILIATE_PRODUCTS.filter((p) => p.category === "sauna").slice(0, 2),
    ...AFFILIATE_PRODUCTS.filter((p) => p.category === "accessories").slice(0, 1),
  ];
}

// Reusable "Practice at Home" affiliate block — update product data in
// lib/affiliates.ts to change links everywhere this renders.
export default function AffiliateSection({ type }: { type: SectionType }) {
  const products = productsForType(type);
  if (products.length === 0) return null;

  return (
    <section className="section affiliate">
      <h2>Practice at Home</h2>
      <p className="lead">
        Can&apos;t make it to a studio? These are our top picks for home cold
        therapy and sauna setups.
      </p>
      <p className="affiliate__disclosure">
        This page contains affiliate links. If you purchase through our
        links, we may earn a small commission at no extra cost to you.
      </p>
      <div className="affiliate__grid">
        {products.map((p) => (
          <div key={p.id} className="affiliate__card">
            <p className="affiliate__card-name">{p.name}</p>
            <p className="affiliate__card-brand">{p.brand}</p>
            <p className="affiliate__card-desc">{p.description}</p>
            <p className="affiliate__card-price">{p.priceRange}</p>
            <a
              className="affiliate__card-cta"
              href={p.amazonUrl}
              target="_blank"
              rel="sponsored noopener noreferrer"
            >
              {ctaLabelFor(p.amazonUrl, p.brand)}
            </a>
          </div>
        ))}
      </div>
    </section>
  );
}
