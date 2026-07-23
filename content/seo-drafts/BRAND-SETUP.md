# IceSoak — Brand Setup & SEO Reference
**Created:** 2026-07-22 | **Profile:** icesoak-seo-worker

---

## Brand Identity

- **Brand slug:** icesoak
- **Site:** icesoak.com
- **Category:** Cold plunge and sauna studio directory
- **Market:** US only (11 metros)

---

## Target Audience

- Health-conscious adults, 25–45
- Biohackers, performance athletes, recovery-focused gym-goers
- Personas: the post-workout professional, the longevity-minded biohacker, the weekend athlete chasing faster recovery

---

## Editorial Voice

Clean, clinical, credible. Think Wirecutter meets wellness.
- No hype language ("amazing", "incredible", "game-changing")
- Cite mechanisms, not just outcomes ("norepinephrine spike" not "mood boost")
- Trust signals: reference PubMed, Huberman, peer-reviewed where relevant
- Specificity over vagueness: temperature ranges, session durations, price ranges
- Never invent studio listings — only reference verified data

---

## Monetization Stack

| Partner | Notes |
|---|---|
| Amazon Associates | Product links — tubs, thermometers, accessories |
| Plunge (plunge.com) | Direct affiliate — flagship cold plunge brand |
| Sweaty Yeti | Affiliate link with sId=16 parameter |
| AWIN | Publisher ID: 2982909 — check AWIN dashboard for active programs |
| Ice Barrel | Direct affiliate |

**Affiliate link rules:**
- Disclose per FTC guidelines (brief, non-intrusive)
- Place product links in "Gear / At-Home Options" sections, not in studio directory sections
- Amazon links: use geotargeted short links where possible

---

## Competitive Landscape

| Competitor | Type | Weakness |
|---|---|---|
| Yelp wellness | Aggregator | Thin content, no cold-plunge topical authority |
| Individual studio sites | Direct | Single-location, no comparison content |
| Reddit wellness threads | UGC | No structured data, not indexable as landing pages |
| Local spa/gym sites | Indirect | Generic — no neighborhood-specific SEO |

**IceSoak edge:** Only US directory with cold-plunge topical authority + 355 pages across 11 metros. Win via content depth + local specificity.

---

## Site Architecture

- **Total pages:** ~355 across 11 US metros
- **Primary URL patterns:**
  - `/cold-plunge/[city]` — metro hub pages
  - `/studio/[slug]` — individual studio detail pages
  - `/[city]/[keyword-slug]/` — neighborhood and intent-specific landing pages (seen in existing keyword files)
- **Priority page types:** City landing pages, studio detail pages, cold plunge vs. sauna guides

---

## Metro Coverage (11 metros)

Rotation: day mod 11. Order confirmed from icesoak.com homepage nav (2026-07-22).

| Index | Metro | Studios |
|---|---|---|
| 0 | Denver, CO | 19 cold plunge / 33 total |
| 1 | Dallas–Fort Worth, TX | 34 |
| 2 | Philadelphia, PA | 34 |
| 3 | Austin, TX | 18 |
| 4 | Chicago, IL | 21 |
| 5 | Atlanta, GA | 16 |
| 6 | Seattle, WA | 17 |
| 7 | Miami, FL | 20 |
| 8 | Nashville, TN | 21 |
| 9 | Los Angeles, CA | 15 |
| 10 | Phoenix, AZ | 10 |

---

## SEO Standards (apply to all output)

### On-Page
- Title tags: 50–60 characters, lead with primary keyword
- Meta descriptions: 140–160 characters, include CTA
- H1: one per page, matches or closely mirrors title keyword
- FAQ sections: always target FAQPage schema
- Internal links: every page links to metro hub + at least 1 related guide

### Schema Markup Targets
- `LocalBusiness` + `GeoCoordinates` on all studio listing pages
- `FAQPage` on all content pages with FAQ sections
- `BreadcrumbList` on all pages
- `ItemList` on roundup/best-of pages
- `Article` with `dateModified` on editorial content

### Content Length Guidelines
| Page Type | Word Count |
|---|---|
| Neighborhood hyper-local page | 400–600 |
| Metro landing page | 700–900 |
| Guide / informational hybrid | 900–1,100 |
| Long-form pillar / best-of | 1,100–1,400 |

### Keyword Research Standards (per metro, 5 keywords)
Each keyword file includes:
- Estimated monthly search volume range
- Competition level (Very Low / Low / Low-Med / Medium / High)
- Search intent classification
- SERP features likely
- Intent analysis paragraph
- Full content brief: title tag, meta, URL slug, word count target, outline, internal/external link recommendations

---

## Output Conventions

- All research files saved to: `/mnt/vault/Research/IceSoak-SEO/`
- Filename format: `YYYY-MM-DD-[Metro]-[type].md`
- Examples:
  - `2026-07-18-Miami-keywords.md`
  - `2026-07-17-Seattle-keywords.md`

---

## Existing Output Index

| Date | Metro | File | Type |
|---|---|---|---|
| 2026-07-17 | Seattle | 2026-07-17-Seattle-keywords.md | Keyword research (5 kws) |
| 2026-07-18 | Miami | 2026-07-18-Miami-keywords.md | Keyword research (5 kws) |
| 2026-07-22 | Denver | 2026-07-22-Denver-keywords.md | Keyword research (5 kws) |

---

*Brand setup authored by IceSoak SEO Specialist | 2026-07-22*
