// Central config for the "Practice at Home" affiliate product section.
// Amazon Associates tag: icesoak-20.
export type AffiliateProduct = {
  id: string;
  name: string;
  description: string;
  category: "cold_plunge" | "sauna" | "accessories";
  amazonUrl: string;
  brand: string;
  priceRange: string;
};

export const AFFILIATE_PRODUCTS: AffiliateProduct[] = [
  {
    id: "ice-barrel-400",
    name: "Ice Barrel 400",
    description: "Vertical cold plunge barrel. Fits most body types, insulated, easy setup.",
    category: "cold_plunge",
    amazonUrl: "https://www.amazon.com/s?k=ice+barrel+cold+plunge&tag=icesoak-20",
    brand: "Ice Barrel",
    priceRange: "$900–$1,200",
  },
  {
    id: "plunge-tub",
    name: "Cold Plunge Tub",
    description: "Filtered, chilled cold plunge tub for daily home use.",
    category: "cold_plunge",
    amazonUrl: "https://www.amazon.com/s?k=cold+plunge+tub+home&tag=icesoak-20",
    brand: "Various",
    priceRange: "$300–$5,000",
  },
  {
    id: "infrared-sauna-blanket",
    name: "Infrared Sauna Blanket",
    description: "Portable infrared sauna blanket for home recovery sessions.",
    category: "sauna",
    amazonUrl: "https://www.amazon.com/s?k=infrared+sauna+blanket&tag=icesoak-20",
    brand: "Various",
    priceRange: "$150–$500",
  },
  {
    id: "sauna-suit",
    name: "Sauna Suit",
    description: "Full-body sauna suit for at-home sweat sessions.",
    category: "sauna",
    amazonUrl: "https://www.amazon.com/s?k=sauna+suit+workout&tag=icesoak-20",
    brand: "Various",
    priceRange: "$20–$80",
  },
  {
    id: "cold-plunge-thermometer",
    name: "Digital Water Thermometer",
    description: "Accurate thermometer to track your plunge temperature.",
    category: "accessories",
    amazonUrl: "https://www.amazon.com/s?k=digital+water+thermometer+cold+plunge&tag=icesoak-20",
    brand: "Various",
    priceRange: "$10–$30",
  },
  {
    id: "ice-pack-set",
    name: "Reusable Ice Packs",
    description: "Flexible ice packs for targeted cold therapy between sessions.",
    category: "accessories",
    amazonUrl: "https://www.amazon.com/s?k=reusable+ice+packs+cold+therapy&tag=icesoak-20",
    brand: "Various",
    priceRange: "$15–$40",
  },
];

export function getProductsByCategory(category: AffiliateProduct["category"]) {
  return AFFILIATE_PRODUCTS.filter((p) => p.category === category);
}
