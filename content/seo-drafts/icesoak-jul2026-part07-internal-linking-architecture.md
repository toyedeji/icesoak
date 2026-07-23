# IceSoak SEO Engagement — Part 07: Internal Linking Architecture
**Engagement ID:** icesoak-jul2026
**Date:** 2026-07-22
**Author:** IceSoak SEO Specialist
**Status:** Active

---

## Purpose

Internal linking is how Google's crawlers understand IceSoak's site hierarchy, how PageRank flows from high-authority pages to conversion pages, and how users navigate from discovery to booking. A well-structured internal link architecture turns 355 loosely connected pages into a coherent topical authority cluster. This document defines the link map, link placement rules, anchor text standards, and the audit process for finding and fixing orphan pages and broken links.

---

## 1. The Link Hierarchy Model

IceSoak uses a four-tier hub-and-spoke model. Authority flows DOWN from the site root and UP from leaf pages. Every tier must link to the tier directly above and below it.

```
TIER 0: Site Root (icesoak.com)
    Links DOWN to all metro hubs and all pillar guide pages

TIER 1: Metro Hub Pages (/cold-plunge/[city]/)
    Links DOWN to neighborhood pages, studio pages, modality guides
    Links UP to: root (via navigation) and pillar guides
    Receives links FROM: root, neighborhood pages, studio pages, best-of pages

TIER 2: Neighborhood Pages (/[city]/[keyword-slug]/)
    Links DOWN to studio pages in or near the neighborhood
    Links UP to metro hub (required)
    Receives links FROM: metro hub, adjacent neighborhood pages, studio pages

TIER 3: Studio Detail Pages (/studio/[slug]/)
    Links UP to metro hub + neighborhood page
    Links ACROSS to 1 modality guide
    Does NOT link down (leaf node)
    Receives links FROM: metro hub, neighborhood page, best-of roundup

TIER 1 (parallel): Guide / Pillar Pages (/guides/[topic]/)
    Links DOWN to related guide cluster pages
    Links ACROSS to metro hub pages (local tie-in)
    Receives links FROM: studio pages, neighborhood pages, product review pages
```

---

## 2. Required Link Sets by Page Type

### Metro Hub Page — must contain all of these

| Destination | Anchor Text Pattern | Max Links |
|---|---|---|
| All neighborhood pages for this metro | "[Neighborhood] cold plunge studios" | All that exist |
| Top 5–8 studio pages (highest rated) | "[Studio Name]" or "[Studio Name] in [Neighborhood]" | 5–8 |
| Contrast therapy guide for this metro | "Contrast therapy in [City]" | 1 |
| Best-of roundup for this metro | "Best cold plunge studios in [City]" | 1 |
| What is contrast therapy (global guide) | "What is contrast therapy?" | 1 |
| Cold plunge safety guide | "Is cold plunge safe?" | 1 |

Metro hub pages should NOT link to:
- Other metro hub pages (cross-metro links dilute local relevance signals)
- Affiliate product pages (keeps directory / commercial separation clean)
- External sites except booking links for studios

### Neighborhood Page — must contain all of these

| Destination | Anchor Text Pattern | Max Links |
|---|---|---|
| Metro hub (same city) | "Browse all [City] cold plunge studios" | 1 (required) |
| Studio pages in/near neighborhood | "[Studio Name]" | 2–4 |
| 1 modality guide | "What is contrast therapy?" or "Cold plunge temperature guide" | 1 |
| Best-of roundup (if published) | "Our top [City] picks" | 1 |
| Adjacent neighborhood page (if exists) | "Cold plunge in [Adjacent Neighborhood]" | 1 optional |

Neighborhood pages should NOT link to:
- Other metro neighborhood pages (wrong geography)
- More than 5 total internal links (small pages; over-linking is noticeable)
- Affiliate pages

### Studio Detail Page — must contain all of these

| Destination | Anchor Text Pattern | Max Links |
|---|---|---|
| Metro hub | "Browse all [City] cold plunge studios" | 1 (required) |
| Neighborhood page (if exists) | "More studios in [Neighborhood]" | 1 |
| 1 modality guide | "What is contrast therapy?" or "Cold plunge temperature" | 1 |
| Best-of roundup (if studio is featured) | "See our top [City] picks" | 1 optional |

Studio pages also include:
- External link to studio's own booking/website (rel="nofollow", separate from editorial links)

### Science / Guide Pages — must contain all of these

| Destination | Anchor Text Pattern | Notes |
|---|---|---|
| Related guide cluster pages | Natural in-text anchor | 3–5 per guide |
| Metro hub pages (2–3 city tie-ins) | "Find cold plunge studios in [City]" | Local directory bridge |
| Comparison page if relevant | "cold plunge vs ice bath" | |
| At-home gear section (Pillar 4) | "at-home cold plunge options" | Only if guide has gear section |

### Best-Of Roundup Pages — must contain all of these

| Destination | Anchor Text Pattern |
|---|---|
| Metro hub | "Browse all [City] studios" |
| Each featured studio page | "[Studio Name] — full listing" |
| Neighborhood pages for featured studios | "[Neighborhood] cold plunge studios" |
| Contrast therapy guide for metro | "Contrast therapy in [City]" |
| Cold plunge temperature guide | "cold plunge temperature guide" |

---

## 3. Link Placement Rules

### In-Content Links
- Place the first internal link in the first 150 words of body content (Google reads early links as high-relevance signals)
- Do not place more than 2 internal links within a single paragraph
- Links should feel natural — they should answer a question the reader is likely to have at that point in the text, not interrupt the reading flow

### Link Density
| Page Word Count | Recommended Internal Links |
|---|---|
| 400–600 (neighborhood) | 3–5 |
| 700–900 (metro hub) | 6–10 |
| 900–1,100 (guide) | 8–12 |
| 1,100–1,400 (best-of/pillar) | 10–15 |

Over-linking past these ranges signals low-quality content to Google. Under-linking leaves PageRank stranded.

### Navigation vs. In-Content Links
- Navigation links (header nav, footer nav) count toward Google's crawl graph but not toward in-content relevance signals
- Always supplement nav links with in-content links for important destinations
- The footer metro list (confirmed on icesoak.com) is a crawl-access link set, not a relevance signal

---

## 4. The IceSoak Link Map (Current Site State)

Based on live site observation, the current link structure is:

### What Exists
- Root → 11 metro hub pages (via nav + homepage metro cards) ✓
- Root → Guides (via nav) ✓
- Root → Modality hubs (/cold-plunge/, /sauna/, etc. — nav links) ✓
- Metro hub → Studio pages (via directory listing cards) ✓
- Root → Compare pages (cold plunge vs ice bath, infrared vs traditional) ✓

### What's Missing (Critical Gaps)
1. **Neighborhood pages: zero** — no neighborhood pages exist; no links to/from neighborhood pages
2. **Studio pages → metro hub: unclear** — studio cards on metro hub link DOWN to studios; do studio pages link back UP to the hub? This must be audited.
3. **Guide pages → metro hubs: likely weak** — existing guides probably don't include in-text links to city directory pages
4. **Best-of roundups: likely absent** — no confirmed `/[city]/best-cold-plunge-[city]/` pages found in site crawl
5. **Cross-pillar links: likely weak** — science guides probably don't link to affiliate review pages

### Priority Link Fixes (Month 1)

| Fix | Action | Impact |
|---|---|---|
| Studio pages missing uplink to metro hub | Add "Browse all [City] studios" link to every studio page | High — consolidates PageRank at hub |
| Guide pages missing city link | Add 2–3 "Find studios in [City]" CTAs to each science guide | High — directory traffic from informational readers |
| Metro hubs missing FAQ internal links | Add in-text links from FAQ answers to relevant guides | Medium — reinforces topical cluster |
| No neighborhood pages | Publish Tier 1 neighborhood pages (Part 04) | Critical — entire hyper-local traffic layer missing |

---

## 5. Sitewide Internal Linking Standards

### Anchor Text Diversity Rule
For any single destination page, use at least 3 different anchor text variations across different linking pages:
- Primary: exact match keyword (`cold plunge studios Denver`)
- Variation 1: partial match (`Denver cold plunge`)
- Variation 2: navigational (`Browse Denver studios`)

Using the same anchor text from 50 different pages looks manipulative. Google expects natural variation.

### Orphan Page Prevention
An orphan page is one that Google can reach only through XML sitemap, not through internal links. Orphan pages lose PageRank entirely.

Rule: No page may be published unless it has at least one internal link pointing to it from a non-sitemap page.

Minimum link requirement before publishing:
- Studio page: linked from metro hub (usually automatic via listing card)
- Neighborhood page: linked from metro hub AND from at least one studio page in the area
- Guide page: linked from at least one metro hub page and one related guide page
- Best-of page: linked from metro hub and from any relevant studio pages featured

### Cross-Metro Linking Rules
- Metro hub pages should NOT link to other metro hub pages
  - Exception: a "Compare cities" or "Available in all 11 metros" contextual mention is fine in footer/nav; NOT in body content of a metro page
- Guide pages CAN reference multiple metros (e.g., "cold plunge studios near you — available in Denver, Seattle, Miami, and 8 more cities")
- Affiliate/gear pages are metro-agnostic and can link to any metro hub as an example

---

## 6. Crawl Budget Optimization

With 355+ pages, Google's crawl budget must be managed efficiently. Key rules:

### Prevent Crawl Waste
- Block filter parameter URLs (`?modality=cold-plunge`, `?sort=rating`) with `robots.txt` disallow or `noindex` canonical
- Pagination: if studio lists paginate, use rel="next/prev" OR consolidate to a single scrollable page
- Session ID URLs: block completely
- Print-friendly versions: canonical to main page

### Sitemap Structure
- Submit a dedicated XML sitemap for studio pages (`/sitemap-studios.xml`)
- Submit a dedicated sitemap for city pages (`/sitemap-cities.xml`)
- Submit a dedicated sitemap for guides (`/sitemap-guides.xml`)
- Exclude any noindex pages from all sitemaps

### Log File Signals (if accessible)
- Pull server access logs monthly and identify pages Googlebot hasn't crawled in > 30 days
- Prioritize those pages for internal link addition (a new inbound link often triggers a recrawl within days)

---

## 7. Link Audit Protocol

Run this audit monthly during Month 1–3, then quarterly.

### Tools (no access required — manual or GSC-based)
- Google Search Console: Coverage report → identify pages Google hasn't indexed
- Google Search Console: Links report → see which internal pages have most inbound links
- Manual crawl: Use Screaming Frog (if available) or a browser crawl script to map all internal links

### Audit Checks

**Orphan detection:**
- Pull all URLs from sitemap
- Cross-reference with all URLs that appear as link targets in the crawl
- Any sitemap URL NOT appearing as a link target from another page = orphan → fix immediately

**Link equity waste:**
- Identify the pages with the most inbound internal links (likely metro hub pages)
- Verify those pages are ALSO passing equity out via links to neighborhood and studio pages
- Hub pages that only receive links but don't pass them back = equity sink

**Anchor text audit:**
- Identify any destination page where more than 60% of inbound anchor text is identical
- Diversify those anchors across future linking pages

**Broken links:**
- Crawl for any internal link returning a 404 or 301 redirect
- 404: Fix the broken link immediately
- 301: Update to point directly to the final URL (avoid redirect chains)

---

## 8. PageRank Flow Model for IceSoak

Approximate authority distribution based on current link structure. Numbers are relative, not absolute PR scores.

```
icesoak.com (root)          PR: 100
  ├── /cold-plunge/denver/  PR: ~25   ← hub receives many external links here ideally
  │     ├── /studio/rok-spas-lodo/         PR: ~8
  │     ├── /studio/sweathouz-south-broadway/  PR: ~8
  │     ├── /denver/sauna-cold-plunge-lodo/     PR: ~6  [after neighborhood pages exist]
  │     └── /denver/best-cold-plunge-denver/    PR: ~6  [after best-of exists]
  ├── /guides/what-is-cold-plunge/  PR: ~20  [highest-volume guide]
  │     └── links out to metro hubs (bridges PR to local pages)
  └── [10 other metro hubs, ~PR 15–25 each]
```

The critical weakness in the current state: guide pages hold high PR but don't route it to city pages. Fixing the guide → metro hub link gap is the single highest-leverage internal linking action in Month 1.

---

## Cross-References

- Part 02: Content Pillars (pillar/cluster architecture maps to the link hierarchy)
- Part 03: Studio Page Optimization (studio page link requirements)
- Part 04: City Landing Page Strategy (city page link requirements)
- Part 06: On-Page SEO Standards (anchor text standards)

---

*IceSoak SEO Engagement icesoak-jul2026 | Part 07 of 12 | 2026-07-22*
