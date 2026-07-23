# IceSoak SEO Engagement — Part 03: Studio Page Optimization
**Engagement ID:** icesoak-jul2026
**Date:** 2026-07-22
**Author:** IceSoak SEO Specialist
**Status:** Active

---

## Purpose

IceSoak has 239 verified studio listings across 11 metros. These are the leaf nodes of the Pillar 2 local directory hierarchy. Each `/studio/[slug]` page is a potential Local Pack ranking asset, a trust signal for the directory's credibility, and an internal link destination that passes authority from neighborhood and metro hub pages. This document defines the full optimization standard for every studio detail page.

---

## 1. Studio Page Anatomy

A fully optimized studio detail page contains eight structural components, in this order:

```
1. Breadcrumb nav             [BreadcrumbList schema]
2. Studio name H1             [matches business name exactly]
3. Quick facts block          [modalities, temp, price, hours — schema-marked]
4. Verification badge         [last-verified date, visible]
5. Map embed                  [single pin, Google Maps or Leaflet]
6. Description section        [150–300 words, factual, IceSoak voice]
7. FAQ block                  [3–5 questions, FAQPage schema]
8. Internal links / CTA row   [metro hub, neighborhood page, booking link]
```

---

## 2. Schema Markup: Full Implementation Spec

Every studio page requires two schema blocks in structured JSON-LD.

### Schema Block 1: LocalBusiness

```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "[Studio Name]",
  "url": "https://icesoak.com/studio/[slug]/",
  "image": "[studio image URL if available]",
  "description": "[1–2 sentence factual description]",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "[street]",
    "addressLocality": "[city]",
    "addressRegion": "[state abbrev]",
    "postalCode": "[zip]",
    "addressCountry": "US"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": [lat],
    "longitude": [lon]
  },
  "telephone": "[phone if verified]",
  "priceRange": "[$ / $$ / $$$]",
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday"],
      "opens": "06:00",
      "closes": "21:00"
    }
  ],
  "amenityFeature": [
    {"@type": "LocationFeatureSpecification", "name": "Cold plunge", "value": true},
    {"@type": "LocationFeatureSpecification", "name": "Infrared sauna", "value": true}
  ],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "[rating]",
    "reviewCount": "[count]"
  }
}
```

**Field population rules:**
- `name`: exact business name as it appears on the studio's own site / Google Business Profile
- `geo`: pull coordinates from Google Maps or OpenStreetMap — do not estimate
- `priceRange`: $ = day pass under $40, $$ = $40–$70, $$$ = over $70
- `openingHoursSpecification`: populate only from verified sources; omit if unverified
- `amenityFeature`: include all confirmed modalities (cold plunge, infrared sauna, traditional sauna, contrast therapy, red-light therapy)
- `aggregateRating`: pull from Google Reviews count and rating at time of verification

### Schema Block 2: BreadcrumbList

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://icesoak.com/"},
    {"@type": "ListItem", "position": 2, "name": "Cold Plunge", "item": "https://icesoak.com/cold-plunge/"},
    {"@type": "ListItem", "position": 3, "name": "[City, State]", "item": "https://icesoak.com/cold-plunge/[city]/"},
    {"@type": "ListItem", "position": 4, "name": "[Studio Name]", "item": "https://icesoak.com/studio/[slug]/"}
  ]
}
```

---

## 3. Quick Facts Block — Data Fields and Standards

The quick facts block is the most important above-the-fold element. It answers the three questions every studio-page visitor has: What do they offer? How cold? How much?

### Required Fields

| Field | Source of truth | Display format | Example |
|---|---|---|---|
| Modalities | Verified from studio site / phone | Icon + text label | Cold plunge / Infrared sauna / Contrast therapy |
| Cold plunge temp range | Studio spec sheet or verified measurement | XX–XX°F | 37–55°F |
| Day pass price | Studio booking page (date-stamped) | from $XX | from $42 |
| Session length options | Studio site | X–X min | 2–10 min |
| Membership available | Yes/No | Boolean badge | Yes |
| Last verified | IceSoak verification date | Month DD, YYYY | July 12, 2026 |
| Rating | Google Reviews at verification | X.X (N reviews) | 4.9 (222) |
| Neighborhood | Standardized IceSoak neighborhood name | [Neighborhood, City, State] | LoDo, Denver, CO |

### Optional Fields (include when verified)

| Field | Display |
|---|---|
| Reservation required | Required / Walk-in welcome |
| Towel service | Included / Available / Not provided |
| Locker facilities | Yes / No |
| Parking | Street / Lot / Garage / None |
| Guided sessions available | Yes / No |
| Private room option | Yes / No |

### Data Freshness Rules
- Verification date must be within 6 months to display "Verified" badge
- Price data older than 3 months displays with a "Prices may have changed — check studio site" note
- Studios with no verification date within 12 months display a "Verification pending" status (as currently seen in site)
- Never show unverified pricing as confirmed pricing

---

## 4. Studio Description: Writing Standard

The studio description section (150–300 words) is the only free-form content on a studio page. It must:

### What to Include
- Physical description of the space (industrial? boutique? medical-grade aesthetic?)
- Specific modalities and their specs where verified
- Notable features that differentiate this studio (private pods vs. shared baths, guided sessions, community events, altitude chamber, red light, etc.)
- Neighborhood context (one sentence: what the location means for access)
- Booking friction note if relevant (reservation required, waitlist, membership-first)

### What Not to Include
- Unverified claims about "best" or "top-rated" without data backing
- Health benefit claims as if IceSoak endorses them (attribute to the studio or frame as what the studio offers)
- Marketing language copied from the studio's own website
- Pricing not independently verified
- Invented details

### Voice Examples

Wrong (hype, unverified): "SweatHouz South Broadway offers an amazing, game-changing contrast therapy experience that will transform your recovery forever."

Right (factual, specific): "SweatHouz South Broadway is a contrast therapy studio on Platt Park's South Broadway strip offering infrared sauna pods, cold plunge tanks (temperature range confirmed at the studio: see quick facts), and red-light therapy. Day passes run from $80; membership unlocks unlimited infrared access with cold plunge credits. Walk-ins accepted; peak-hour slots typically require reservation via the SweatHouz app."

### Length by Studio Type
- Standalone cold plunge studio (single modality): 150–200 words
- Full contrast therapy studio (sauna + cold + other): 200–275 words
- Multi-modality wellness center (spa + cold + sauna + recovery): 250–300 words

---

## 5. FAQ Block — Studio Page Questions

Each studio page should have 3–5 FAQ items targeting common pre-visit questions. These are FAQPage schema targets and can appear in Google's People Also Ask results.

### Question Templates by Studio Type

**For cold plunge-only studios:**
- "How cold is the cold plunge at [Studio Name]?"
- "Do I need a membership to use [Studio Name]?"
- "How long can I stay in the cold plunge at [Studio Name]?"
- "Is [Studio Name] open to walk-ins?"

**For contrast therapy / sauna + cold plunge studios:**
- "Does [Studio Name] have both sauna and cold plunge?"
- "What is the contrast therapy protocol at [Studio Name]?"
- "How much does a day pass cost at [Studio Name]?"
- "Can I do unlimited sessions at [Studio Name] with a membership?"

**For multi-modality wellness centers:**
- "What recovery services does [Studio Name] offer?"
- "Is red-light therapy available at [Studio Name]?"
- "Does [Studio Name] offer guided contrast therapy sessions?"

### Answer Standards
- Answers must be 40–80 words — long enough to be informative, short enough to appear in a PAA snippet
- Use verified data only — if temperature is unverified, answer with "Contact the studio directly for current plunge temperatures"
- Always include a practical follow-up (pricing anchor, booking tip, or what to bring)

---

## 6. Internal Link Standards for Studio Pages

Every studio page must contain exactly these internal links:

| Link | Anchor text example | Destination |
|---|---|---|
| Metro hub | "Browse all Denver cold plunge studios" | `/cold-plunge/denver/` |
| Neighborhood page (if exists) | "More studios in LoDo" | `/denver/sauna-cold-plunge-lodo/` |
| Modality guide | "What is contrast therapy?" | `/guides/what-is-contrast-therapy/` |
| Best-of roundup (if published) | "See our top Denver picks" | `/denver/best-cold-plunge-denver/` |

Do not add more than 4–5 internal links per studio page. Over-linking dilutes link equity and clutters the user experience.

### External Link (Booking CTA)
- Link to the studio's own booking page or website
- Use `rel="nofollow"` — we are referring traffic, not endorsing as an editorial backlink
- Anchor text: "Visit [Studio Name] website →" or "Book at [Studio Name] →"
- Place in a clearly labeled CTA row, separate from editorial content

---

## 7. Title Tag and Meta Description: Studio Page Formulas

### Title Tag Formula
`[Studio Name] — [City, State] Cold Plunge & Sauna | IceSoak`

Rules:
- Keep under 60 characters total
- If studio name + city + suffix exceeds 60: shorten suffix to `| IceSoak`
- Lead with studio name (navigational intent — users are searching the studio name)
- Include primary modality where space allows

Examples:
- `ROK SPAS — LoDo Denver Cold Plunge & Sauna | IceSoak` (52 chars) ✓
- `SweatHouz South Broadway — Denver Contrast Therapy | IceSoak` (60 chars) ✓
- `The Cove Sauna and Cold Plunge — Denver | IceSoak` (49 chars) ✓

### Meta Description Formula
`[Studio Name] in [Neighborhood, City] offers [modalities]. [One differentiating fact: price / temp / feature]. Verified listing on IceSoak — [CTA].`

Rules:
- 140–160 characters
- Include at least one specific data point (price, temperature, modality)
- Include "IceSoak" as the trust brand
- End with a directional CTA

Examples:
- `ROK SPAS in LoDo Denver offers traditional sauna and cold plunge at 37–55°F. Day passes from $42. Verified listing on IceSoak — see hours and book.` (149 chars) ✓
- `SweatHouz South Broadway in Platt Park offers infrared sauna, cold plunge, and red-light therapy. From $80/day. Verified on IceSoak.` (133 chars) ✓

---

## 8. Studio Page Audit Protocol

Run this audit on every existing studio page before declaring it "optimized." Log results to a tracking sheet.

### Audit Checklist

**Technical**
- [ ] Title tag present, 50–60 characters, formula-compliant
- [ ] Meta description present, 140–160 characters
- [ ] H1 present, matches studio name
- [ ] Canonical URL set (no duplicate content from filter parameters)
- [ ] Page loads under 2.5s on mobile (LCP)
- [ ] No broken internal links
- [ ] LocalBusiness schema present and valid (test with Google Rich Results Test)
- [ ] BreadcrumbList schema present
- [ ] FAQPage schema present (if FAQ block exists)

**Content**
- [ ] Quick facts block complete (modalities, temp, price, verification date)
- [ ] Description 150–300 words, IceSoak voice, no invented claims
- [ ] FAQ block: 3–5 questions with 40–80 word answers
- [ ] Verification date displayed, within 6 months OR "Verification pending" shown

**Internal Links**
- [ ] Link to metro hub present
- [ ] Link to neighborhood page present (if page exists)
- [ ] Link to modality guide present
- [ ] External booking link present with rel="nofollow"

**Local SEO**
- [ ] GeoCoordinates schema matches actual studio address
- [ ] Studio name in schema matches Google Business Profile name exactly
- [ ] AggregateRating present when rating data is verified

### Audit Priority Order
Audit by studio rating × review count (highest-rated, most-reviewed studios first — they receive the most branded search traffic and must be optimized before lower-ranked listings).

Top priority studios to audit (from Denver data collected):
1. R3 Spa: Sauna + Cold Plunge (4.9, 380 reviews)
2. Red Rock Sauna (5.0, 250 reviews)
3. SweatHouz South Broadway Contrast Therapy (4.9, 222 reviews)
4. The Cove Sauna and Cold Plunge (5.0, 151 reviews)
5. Recovery Lounge & Spa (4.9, 130 reviews)

Replicate priority ordering for all 11 metros: sort by rating count descending, audit top 10 per metro in Month 1.

---

## 9. Verification Workflow

Studio data has a shelf life. A studio that was verified 8 months ago may have changed hours, prices, or ownership. IceSoak's trust signal depends on freshness.

### Verification Cadence
- Top-rated studios (4.8+, 100+ reviews): re-verify every 3 months
- Mid-tier studios (4.0–4.7, 30–99 reviews): re-verify every 6 months
- Low-volume studios (< 30 reviews): re-verify annually
- Studios with "Verification pending" status: prioritize for initial verification

### Verification Methods (in preference order)
1. Direct studio website check (pricing, hours, modalities)
2. Google Business Profile (hours, phone, address)
3. Studio's booking platform (Mindbody, FitReserve, direct booking — confirm current prices)
4. Phone call (for temperature specs and session options not published online)

### What Changes Trigger Immediate Re-verification
- Studio changes ownership (new name, rebrand)
- Studio adds or removes a modality (e.g., adds red-light therapy or removes cold plunge)
- Price change reported by user via IceSoak feedback
- Google Business Profile shows "Permanently closed" or "Temporarily closed"

---

## Cross-References

- Part 02: Content Pillars (Pillar 2 — studio pages are leaf nodes)
- Part 06: On-Page SEO Standards (technical standards apply)
- Part 07: Internal Linking Architecture (studio page link rules)

---

*IceSoak SEO Engagement icesoak-jul2026 | Part 03 of 12 | 2026-07-22*
