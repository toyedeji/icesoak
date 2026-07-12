import { AFFILIATE_PRODUCTS, type AffiliateProduct } from "@/lib/affiliates";

type SectionType = "cold_plunge" | "sauna" | "general";

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
              View on Amazon →
            </a>
          </div>
        ))}
      </div>
    </section>
  );
}
