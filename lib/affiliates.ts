// Central config for the "Practice at Home" affiliate product section.
// Amazon Associates tag: icesoak-20.
// Other affiliate links: Plunge (Impact.com), Sweaty Yeti (direct), Ice Barrel (AWIN - pending)

export type AffiliateProduct = {
  id: string;
  name: string;
  description: string;
  category: "cold_plunge" | "sauna" | "accessories";
  amazonUrl: string;
  brand: string;
  priceRange: string;
  couponCode?: string;
  couponNote?: string;
};

export const AFFILIATE_PRODUCTS: AffiliateProduct[] = [
  {
    id: "plunge-tub",
    name: "Plunge Cold Plunge",
    description: "Temperature-controlled cold plunge tub. No ice needed — plug in and plunge daily.",
    category: "cold_plunge",
    amazonUrl: "https://plunge.pxf.io/c/7476185/1068315/13696",
    brand: "Plunge",
    priceRange: "$1,290–$4,990",
  },
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
    id: "sweaty-yeti-sauna",
    name: "Sweaty Yeti Outdoor Sauna",
    description: "Premium outdoor sauna and cold plunge combos. Built for serious home wellness setups.",
    category: "sauna",
    amazonUrl: "https://sweatyyetisauna.com/?sId=16",
    brand: "Sweaty Yeti",
    priceRange: "$3,000–$15,000",
    couponCode: "icesoak5",
    couponNote: "5% off with code icesoak5",
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
