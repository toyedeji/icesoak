# IceSoak SEO Engagement — Part 01: Keyword Research Framework
**Engagement ID:** icesoak-jul2026
**Date:** 2026-07-22
**Author:** IceSoak SEO Specialist
**Status:** Active

---

## Purpose

This document defines the keyword research system for IceSoak across all 11 US metros. It establishes the universe of keyword archetypes, a repeatable prioritization model, per-metro opportunity maps with primary targets, the content brief template used across the engagement, and the research cadence. All subsequent keyword research files (produced by the daily cron rotation) conform to this framework.

---

## 1. Keyword Archetype Universe

IceSoak operates at the intersection of local directory SEO and informational wellness content. Every keyword it can realistically rank for falls into one of six archetypes:

### Archetype A: Metro Head Terms
Format: `cold plunge studio [city]` / `cold plunge [city]`
Intent: Local commercial — ready to visit or book
Volume: Highest per metro (typically 400–900/mo for top metros)
Competition: Low–Medium (Yelp + GBP dominate; no editorial authority competitor)
Priority: Always publish first. These are the metro hub pages.

Examples:
- `cold plunge studio Denver`
- `cold plunge Miami`
- `cold plunge studios Chicago`
- `cold plunge Los Angeles`

### Archetype B: Modality Combination Terms
Format: `sauna and cold plunge [city]` / `contrast therapy [city]` / `infrared sauna cold plunge [city]`
Intent: Informational / commercial investigation — mid-funnel
Volume: Medium (200–600/mo for active metros)
Competition: Low (SweatHouz and individual studios rank; no neutral guide exists)
Priority: Second tier — publish after head term hub page is indexed.

Examples:
- `contrast therapy Denver`
- `infrared sauna and cold plunge Seattle`
- `sauna cold plunge Nashville`

### Archetype C: Neighborhood / Hyper-Local Terms
Format: `cold plunge [neighborhood] [city]` / `ice bath [neighborhood] [city]`
Intent: Local navigational / transactional — highest conversion rate
Volume: Low per neighborhood (50–200/mo) but stackable across 5–10 neighborhoods per metro
Competition: Very Low (zero dedicated pages exist in almost all cases)
Priority: Third tier — templated and published in batches per metro.

Examples:
- `cold plunge Cherry Creek Denver`
- `cold plunge studio Capitol Hill Seattle`
- `ice bath recovery Brickell Miami`
- `cold plunge LoDo Denver`
- `cold plunge Midtown Atlanta`

### Archetype D: Informational / Performance Science Terms
Format: `cold plunge [city] [specific benefit or use case]`
Intent: Informational — research phase, top-of-funnel
Volume: Variable (100–350/mo)
Competition: Very Low for city-specific variants (national blogs compete for generic versions)
Priority: High when a Denver-unique angle exists (altitude, heat, weather); medium otherwise.

Examples:
- `ice bath Denver altitude recovery`
- `cold plunge Phoenix heat recovery`
- `cold water therapy benefits Austin athletes`

### Archetype E: "Best Of" / Listicle Terms
Format: `best cold plunge studios [city] [year]` / `top ice bath spots [city]`
Intent: Commercial investigation — curated recommendation
Volume: Medium (150–500/mo for major metros)
Competition: Medium (Yelp, TimeOut, local blogs rank; beatable with topical authority + fresh data)
Priority: High for metros with 15+ verified studios. Requires quarterly freshness updates.

Examples:
- `best cold plunge studios Seattle 2026`
- `best contrast therapy gyms Dallas`
- `top cold plunge spots Los Angeles`

### Archetype F: Transactional / Membership / Pricing Terms
Format: `cold plunge membership [city]` / `contrast therapy studio [city] membership` / `cold plunge day pass [city]`
Intent: Transactional — bottom of funnel, highest LTV signal
Volume: Low–Medium (80–250/mo)
Competition: Very Low (studios rarely publish structured pricing/membership comparison content)
Priority: High conversion value; publish after neighborhood pages are live.

Examples:
- `contrast therapy membership Seattle`
- `cold plunge day pass Denver`
- `cold plunge monthly membership Chicago`

---

## 2. Keyword Prioritization Model

Each keyword is scored on four axes. The composite score determines publish sequence within a metro.

### Scoring Rubric

| Axis | Weight | Scale |
|---|---|---|
| Search Volume | 30% | 1 (< 50/mo) to 5 (> 500/mo) |
| Competition Gap | 30% | 1 (High competition) to 5 (Very Low) |
| Conversion Proximity | 25% | 1 (Awareness) to 5 (Transactional) |
| Topical Cluster Fit | 15% | 1 (Tangential) to 5 (Core) |

**Composite Score = (Vol × 0.30) + (Gap × 0.30) + (Conv × 0.25) + (Cluster × 0.15)**

### Worked Example — Denver

| Keyword | Vol | Gap | Conv | Cluster | Score |
|---|---|---|---|---|---|
| cold plunge studio Denver | 5 | 3 | 4 | 5 | **4.10** |
| contrast therapy Denver | 4 | 4 | 3 | 5 | **3.95** |
| ice bath Denver altitude recovery | 2 | 5 | 3 | 4 | **3.35** |
| cold plunge Cherry Creek Denver | 2 | 5 | 5 | 4 | **3.80** |
| sauna cold plunge LoDo Denver | 2 | 5 | 4 | 4 | **3.55** |

Publish sequence: 1 → 2 → 4 → 5 → 3 (metro hub first, then contrast guide, then neighborhood pages, then informational).

### Standing Rules That Override Scoring

1. Metro hub page (Archetype A) always publishes first — it is the internal link destination for all subsequent pages.
2. "Best of" pages (Archetype E) require at least 10 verified studio listings before publishing — thin roundups hurt credibility.
3. Altitude / climate hooks (Archetype D) get bumped when the city has a unique environmental differentiator (Denver, Phoenix, Miami, Seattle).
4. Neighborhood pages (Archetype C) are templated and batch-published in groups of 3–5 to maximize crawl efficiency.

---

## 3. Per-Metro Keyword Opportunity Maps

For each metro: primary head term, top opportunity archetype, unique content hook, and estimated keyword universe size.

### Metro 0: Denver, CO — 33 studios, 19 cold plunge

| Layer | Target | Notes |
|---|---|---|
| Head term | `cold plunge studio Denver` (500–800/mo) | Hub page anchor |
| Modality combo | `contrast therapy Denver` (350–600/mo) | SweatHouz gap |
| Best-of | `best cold plunge studios Denver 2026` (200–400/mo) | Yelp beatable |
| Neighborhoods | LoDo, Cherry Creek, Platt Park, Lakewood, Aurora, Englewood, RiNo | 6–8 pages |
| Unique hook | Altitude recovery — 5,280 ft, EPO, breathing protocols | Zero competitor content |
| Est. keyword universe | 35–45 rankable terms | — |

Files produced: 2026-07-22-Denver-keywords.md (5 keywords, full briefs)

### Metro 1: Dallas–Fort Worth, TX — 34 studios

| Layer | Target | Notes |
|---|---|---|
| Head term | `cold plunge studio Dallas` (400–700/mo) | Split DFW: Dallas + Fort Worth pages |
| Modality combo | `contrast therapy Dallas` / `infrared sauna cold plunge DFW` | Chain studio presence (SweatHouz) |
| Best-of | `best cold plunge gyms Dallas 2026` | Yelp + D Magazine occupy top spots |
| Neighborhoods | Uptown, Deep Ellum, Frisco, Plano, Fort Worth Near Southside | 6–8 pages |
| Unique hook | Heat recovery — Dallas summer heat index pushes cold therapy as necessity not novelty | |
| Est. keyword universe | 40–55 rankable terms | Largest studio count = highest volume |

### Metro 2: Philadelphia, PA — 34 studios

| Layer | Target | Notes |
|---|---|---|
| Head term | `cold plunge studio Philadelphia` (300–550/mo) | |
| Modality combo | `contrast therapy Philly` / `sauna cold plunge Philadelphia` | |
| Best-of | `best cold plunge studios Philadelphia 2026` | |
| Neighborhoods | Center City, Fishtown, Rittenhouse Square, South Philly, Main Line | 5–7 pages |
| Unique hook | Sports recovery — Eagles/Phillies/76ers fan culture; athlete recovery framing | |
| Est. keyword universe | 35–45 rankable terms | |

### Metro 3: Austin, TX — 18 studios

| Layer | Target | Notes |
|---|---|---|
| Head term | `cold plunge studio Austin` (350–600/mo) | Strong biohacker/tech audience |
| Modality combo | `contrast therapy Austin` / `sauna cold plunge Austin` | |
| Best-of | `best cold plunge Austin 2026` | Austin Chronicle, Do512 are beatable |
| Neighborhoods | East Austin, South Congress, Domain, Cedar Park | 4–5 pages |
| Unique hook | Biohacker culture — Austin's tech/entrepreneur demographic responds to performance + longevity framing | |
| Est. keyword universe | 28–38 rankable terms | Smaller studio count limits neighborhood expansion |

### Metro 4: Chicago, IL — 21 studios

| Layer | Target | Notes |
|---|---|---|
| Head term | `cold plunge studio Chicago` (450–750/mo) | High-volume market |
| Modality combo | `contrast therapy Chicago` / `infrared sauna cold plunge Chicago` | |
| Best-of | `best cold plunge gyms Chicago 2026` | Chicago Mag, Eater rank here |
| Neighborhoods | River North, Lincoln Park, Wicker Park, West Loop, Andersonville | 5–7 pages |
| Unique hook | Winter cold as cultural asset — Chicagoans already normalize cold; position indoor plunge as controlled, year-round version | |
| Est. keyword universe | 38–50 rankable terms | |

### Metro 5: Atlanta, GA — 16 studios

| Layer | Target | Notes |
|---|---|---|
| Head term | `cold plunge studio Atlanta` (300–500/mo) | |
| Modality combo | `contrast therapy Atlanta` / `sauna cold plunge Buckhead` | |
| Best-of | `best cold plunge Atlanta 2026` | |
| Neighborhoods | Buckhead, Midtown, Virginia-Highland, Decatur, Sandy Springs | 5–6 pages |
| Unique hook | Heat/humidity angle (similar to Miami) — Atlanta summer conditions make cold plunge "essential not optional" | |
| Est. keyword universe | 28–38 rankable terms | |

### Metro 6: Seattle, WA — 17 studios

| Layer | Target | Notes |
|---|---|---|
| Head term | `cold plunge studio Seattle` (350–600/mo) | |
| Modality combo | `infrared sauna and cold plunge Seattle` (300–600/mo) | Strong modality combo search |
| Best-of | `best cold plunge studios Seattle 2026` (250–500/mo) | Medium competition |
| Neighborhoods | Capitol Hill, Ballard, South Lake Union, Fremont, Bellevue, West Seattle | 6–8 pages |
| Unique hook | Puget Sound cold water culture + tech-worker biohacking (Amazon/Microsoft corridor) | |
| Est. keyword universe | 35–45 rankable terms | |

Files produced: 2026-07-17-Seattle-keywords.md (5 keywords, full briefs)

### Metro 7: Miami, FL — 20 studios

| Layer | Target | Notes |
|---|---|---|
| Head term | `cold plunge studio Miami` (400–700/mo) | |
| Modality combo | `contrast therapy Miami` / `sauna cold plunge Miami Beach` | |
| Best-of | `best cold plunge Miami 2026` | Miami New Times, TimeOut Miami rank here |
| Neighborhoods | Miami Beach, Brickell, Wynwood, Coral Gables, Doral | 5–7 pages |
| Unique hook | Heat/humidity as pain point — cold plunge is MORE effective in hot climates; counter-narrative against "why plunge in Miami?" | |
| Est. keyword universe | 35–45 rankable terms | |

Files produced: 2026-07-18-Miami-keywords.md (5 keywords, full briefs)

### Metro 8: Nashville, TN — 21 studios

| Layer | Target | Notes |
|---|---|---|
| Head term | `cold plunge studio Nashville` (250–450/mo) | Growing market |
| Modality combo | `contrast therapy Nashville` / `sauna cold plunge Nashville` | |
| Best-of | `best cold plunge Nashville 2026` | Nashville Scene, local wellness blogs |
| Neighborhoods | The Gulch, East Nashville, 12 South, Brentwood, Franklin | 4–6 pages |
| Unique hook | Fast-growing city, transplant audience — frame Nashville cold plunge as part of the city's wellness maturation alongside its food/music identity | |
| Est. keyword universe | 30–40 rankable terms | |

### Metro 9: Los Angeles, CA — 15 studios

| Layer | Target | Notes |
|---|---|---|
| Head term | `cold plunge studio Los Angeles` (500–900/mo) | Highest ceiling but most competitive |
| Modality combo | `contrast therapy LA` / `infrared sauna cold plunge Los Angeles` | |
| Best-of | `best cold plunge studios Los Angeles 2026` | LA Times, Eater, Well+Good dominate |
| Neighborhoods | Venice, Santa Monica, Beverly Hills, Silver Lake, West Hollywood, Culver City | 6–8 pages |
| Unique hook | Celebrity/biohacker culture — Huberman, Bryan Johnson, wellness influencer ecosystem makes LA the aspirational cold plunge market | |
| Est. keyword universe | 40–55 rankable terms | Fewer studios (15) limits neighborhood page depth |
| Caution | Higher competition — LA needs more backlinks than other metros to break through "best of" SERPs | |

### Metro 10: Phoenix, AZ — 10 studios

| Layer | Target | Notes |
|---|---|---|
| Head term | `cold plunge studio Phoenix` (200–400/mo) | |
| Modality combo | `contrast therapy Phoenix` / `cold plunge Scottsdale` | Scottsdale is the premium wellness hub |
| Best-of | `best cold plunge Phoenix 2026` | Low competition |
| Neighborhoods | Scottsdale, Tempe, Chandler, Arcadia, North Phoenix | 4–5 pages |
| Unique hook | Extreme heat recovery — Phoenix summer temps (110°F+) make cold plunge a functional necessity; strongest heat-angle narrative of any metro | |
| Est. keyword universe | 22–30 rankable terms | Smallest studio count; focus on Scottsdale premium angle |

---

## 4. Keyword Research Production Schedule

The daily cron rotation (day mod 11) generates one metro keyword file per day — 5 keywords with full content briefs. At the current rotation rate, the full 11-metro initial pass completes in 11 days.

### Completion Tracking

| Metro | Index | Status | File |
|---|---|---|---|
| Denver, CO | 0 | DONE | 2026-07-22-Denver-keywords.md |
| Dallas–Fort Worth, TX | 1 | Pending | — |
| Philadelphia, PA | 2 | Pending | — |
| Austin, TX | 3 | Pending | — |
| Chicago, IL | 4 | Pending | — |
| Atlanta, GA | 5 | Pending | — |
| Seattle, WA | 6 | DONE | 2026-07-17-Seattle-keywords.md |
| Miami, FL | 7 | DONE | 2026-07-18-Miami-keywords.md |
| Nashville, TN | 8 | Pending | — |
| Los Angeles, CA | 9 | Pending | — |
| Phoenix, AZ | 10 | Pending | — |

Second-pass rotation (neighborhoods, "best of" pages, informational long-tails) begins after all 11 metros have initial keyword files.

---

## 5. Keyword Research Quality Checklist

Every metro keyword file must pass this checklist before being considered complete:

- [ ] 5 keywords minimum, spanning at least 3 different archetypes (A–F)
- [ ] Each keyword has: volume range, competition level, intent classification, SERP features likely
- [ ] Each keyword has an intent analysis paragraph (3–5 sentences) explaining WHY searchers use this query
- [ ] Each keyword has a full content brief: title tag (50–60 chars), meta description (140–160 chars), target URL slug, word count target, section outline with H2 structure, internal links list, external links list
- [ ] At least 1 keyword targets a featured snippet or PAA box
- [ ] At least 1 keyword is a hyper-local neighborhood term
- [ ] At least 1 keyword uses a metro-specific content hook (climate, culture, sports, geography)
- [ ] Summary table at top with priority flags
- [ ] Quick-win recommendations section at bottom with recommended publishing cadence

---

## 6. Standard Content Brief Template

All keyword research files use this template structure for each keyword brief. Copy/paste and fill per keyword.

```
## Keyword N: `[keyword phrase]`

| Field | Detail |
|---|---|
| **Estimated Monthly Searches** | [range] |
| **Competition Level** | [Very Low / Low / Low-Med / Medium / High] |
| **Search Intent** | [classification] |
| **SERP Features Likely** | [features] |

### Intent Analysis
[3–5 sentence paragraph explaining searcher mindset, what they want, and why IceSoak wins]

### Content Brief

**Title Tag:** `[title]` *([N] characters)*
**Meta Description:** `[meta]` *([N] characters)*
**Target URL Slug:** `/[path]/`
**Word Count Target:** [range] words
**Internal Links:** [list]

#### Outline
1. **H1:** [heading]
2. **H2:** [section]
   - [bullet points of content]
[continue...]

**FAQ Schema Block**
- "[question 1]"
- "[question 2]"
[...]

**CTA:** [call to action text]
**External Links:** [sources]
**Schema Markup:** [types to implement]
```

---

## 7. Keyword Universe Size Estimate

Across all 11 metros, the full rankable keyword universe for IceSoak is estimated at:

| Category | Est. Keywords |
|---|---|
| Metro head terms (1–2 per metro) | 15–20 |
| Modality combination terms (2–3 per metro) | 25–35 |
| Neighborhood / hyper-local terms (5–10 per metro) | 60–110 |
| Informational / science terms (1–2 per metro) | 15–25 |
| "Best of" / listicle terms (1–2 per metro) | 12–18 |
| Membership / pricing / transactional terms (1–2 per metro) | 12–18 |
| **Total** | **139–226 rankable terms** |

At 5 keywords per cron run, with 11 metros per pass and 3 passes to cover the full universe:
- Pass 1 (head terms + top modality combos): 55 keywords over ~11 days
- Pass 2 (neighborhoods + best-of): 55 keywords over ~11 days
- Pass 3 (informational + transactional): 55 keywords over ~11 days
- Full universe covered in approximately 33 production days

---

## 8. Keyword-to-Page Mapping Logic

Not every keyword gets its own page. Mapping rules:

### One Page Per Keyword When:
- Volume > 150/mo AND distinct intent from nearby keywords
- Neighborhood terms (always standalone — Local Pack eligibility requires it)
- "Best of" terms (standalone roundup page with ItemList schema)

### Consolidate Multiple Keywords Into One Page When:
- Volume < 100/mo AND intent overlap > 80% (e.g., `ice bath Dallas` and `cold water immersion Dallas`)
- Informational terms with the same core topic but different phrasings — target the primary keyword, optimize for secondary as semantic variation
- Pricing/membership terms — one pricing guide per metro, targeting 2–3 similar queries

### Hub-and-Spoke Consolidation Model
Each metro has:
- 1 hub page (metro head term, all modalities)
- 3–5 spoke pages (neighborhood, best-of, contrast therapy guide, informational)
- N studio detail pages (from /studio/[slug] structure)

The hub links to all spokes. Every spoke links back to the hub. Studio pages link up to both the metro hub and the relevant neighborhood spoke page.

---

## Cross-References

- Brand config: BRAND-SETUP.md
- Denver keyword research: 2026-07-22-Denver-keywords.md
- Seattle keyword research: 2026-07-17-Seattle-keywords.md
- Miami keyword research: 2026-07-18-Miami-keywords.md
- Next: Part 02 — Content Pillars

---

*IceSoak SEO Engagement icesoak-jul2026 | Part 01 of 12 | 2026-07-22*
