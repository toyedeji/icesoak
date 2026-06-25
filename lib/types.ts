export interface Studio {
  id: string;
  name: string;
  metro: string;
  city: string;
  lat: number | null;
  lng: number | null;
  status: string;
  brand?: string | null;
  state?: string | null;
  neighborhood?: string | null;
  address?: string | null;
  website?: string | null;
  booking_url?: string | null;
  instagram?: string | null;
  modalities?: string[] | null;
  plunge_temp_f_min?: number | null;
  plunge_temp_f_max?: number | null;
  format?: string | null;
  session_style?: string | null;
  access?: string | null;
  day_pass_price_usd?: number | null;
  membership_from_usd?: number | null;
  amenities?: string[] | null;
  google_place_id?: string | null;
  google_rating?: number | null;
  google_reviews_count?: number | null;
  source_urls?: string[] | null;
  last_verified?: string | null;
  source?: string | null;
}

export interface Metro {
  metro: string;
  slug: string;
  name: string;
  state: string;
  stateName: string;
  lat: number;
  lng: number;
  dense: boolean;
  blurb: string;
}

export interface QuestionSection {
  h2: string;
  body: string;
}

export interface Faq {
  q: string;
  a: string;
}

export interface Question {
  slug: string;
  question: string;
  category: string;
  updated: string;
  author: string;
  capsule: string;
  sections: QuestionSection[];
  faqs?: Faq[];
}
