# IceSoak SEO Engagement — Part 06: On-Page SEO Standards
**Engagement ID:** icesoak-jul2026
**Date:** 2026-07-22
**Author:** IceSoak SEO Specialist
**Status:** Active

---

## Purpose

This document is the single authoritative on-page SEO standard for every page on icesoak.com. It covers title tags, meta descriptions, heading structure, schema markup, Core Web Vitals, image optimization, URL structure, canonical handling, and the pre-publish checklist. All content produced in this engagement is checked against these standards before being considered complete.

---

## 1. Title Tag Standards

### Rules
- Length: 50–60 characters (Google displays ~600px; 60 chars is the safe ceiling)
- Lead with the primary keyword — do not bury it after the brand name
- Brand suffix: `| IceSoak` (9 characters including space and pipe)
- Never truncate mid-word — count characters including spaces
- No ALL CAPS, no emoji, no special characters except hyphens and pipes
- Every title must be unique across the entire site — no duplicates

### Formulas by Page Type

| Page Type | Formula | Example |
|---|---|---|
| Metro hub | `Cold Plunge Studios in [City, State] \| IceSoak` | `Cold Plunge Studios in Denver, CO \| IceSoak` (46 chars) |
| Neighborhood | `Cold Plunge in [Neighborhood], [City] \| IceSoak` | `Cold Plunge in LoDo, Denver \| IceSoak` (38 chars) |
| Studio detail | `[Studio Name] — [City] Cold Plunge \| IceSoak` | `ROK SPAS — Denver Cold Plunge \| IceSoak` (41 chars) |
| Best-of roundup | `Best Cold Plunge Studios in [City] [Year] \| IceSoak` | `Best Cold Plunge Studios in Denver 2026 \| IceSoak` (51 chars) |
| Science pillar | `[Question as phrase] — IceSoak Guide` | `Cold Plunge Temperature Guide — IceSoak` (40 chars) |
| Product review | `[Product Name] Review ([Year]) \| IceSoak` | `Plunge Cold Plunge Review (2026) \| IceSoak` (44 chars) |
| Comparison | `[A] vs [B]: [Short verdict] \| IceSoak` | `Cold Plunge vs Ice Bath \| IceSoak` (34 chars) |

### Title Tag Audit Flags
- Flag: Title over 60 characters → shorten suffix or abbreviate city
- Flag: Title missing primary keyword → rebuild
- Flag: Duplicate title across two pages → differentiate or consolidate pages
- Flag: Keyword stuffing (more than 1–2 instances of a keyword) → rewrite

---

## 2. Meta Description Standards

### Rules
- Length: 140–160 characters (optimal for display in SERPs without truncation)
- Must include: primary keyword (naturally), a specific data point or differentiator, and a CTA
- No duplicate meta descriptions
- Do not repeat the title tag verbatim — add new information
- Write for click-through rate, not just keyword inclusion
- Include the IceSoak brand name

### Formulas by Page Type

| Page Type | Formula |
|---|---|
| Metro hub | `Find [N]+ verified cold plunge studios in [City]. Compare modalities, prices, and neighborhoods. IceSoak — no hype, just the numbers.` |
| Neighborhood | `Find cold plunge and recovery studios in [Neighborhood], [City]. Compare verified options — temperatures, pricing, and session details.` |
| Studio detail | `[Studio Name] in [Neighborhood, City] offers [modalities]. [One data point]. Verified on IceSoak — see hours and book.` |
| Best-of | `The best cold plunge studios in [City] for [Year] — ranked by IceSoak. Compare water temp, pricing, and amenities. Verified listings only.` |
| Science pillar | `[Question answered in 1 sentence]. IceSoak breaks down the science, the protocols, and [relevant local tie-in].` |
| Product review | `Is [Product] worth it? We review the specs, temperature performance, and long-term value. Honest assessment — no affiliate spin.` |

---

## 3. Heading Structure (H1–H4)

### H1 Rules
- One and only one H1 per page — no exceptions
- Must match or closely mirror the title tag primary keyword
- Do not use the brand name in H1 (that's what the title tag is for)
- Examples:
  - Title: `Cold Plunge Studios in Denver, CO | IceSoak`
  - H1: `Cold Plunge Studios in Denver, CO` ✓
  - H1: `IceSoak Denver Cold Plunge Directory` ✗ (brand name in H1 wastes the keyword slot)

### H2 Rules
- Each major section gets an H2
- H2s should collectively outline the page topic — if you read only the H2s, you should understand what the page covers
- Include the target keyword or a close semantic variant in at least one H2
- For FAQ sections: `Frequently Asked Questions About Cold Plunge in [City]` is a valid H2

### H3 Rules
- Use for subsections within H2 sections
- On best-of pages: each studio gets an H3 (studio name only, no keyword stuffing)
- On comparison pages: each product gets an H3

### H4 and Below
- Use sparingly — only for sub-subsections in very long guides
- If you're using H4s in a neighborhood page, the page is probably too long

### Heading Hierarchy Example — Metro Hub Page
```
H1: Cold Plunge Studios in Denver, CO
  H2: Denver's Cold Plunge Scene
  H2: What to Look for in a Denver Cold Plunge Studio
  H2: IceSoak-Verified Studios in Denver
  H2: Pricing Guide — Cold Plunge in Denver
  H2: Cold Plunge at Altitude: What Denver Athletes Need to Know
  H2: Denver Neighborhoods with Cold Plunge Studios
    H3: LoDo
    H3: Cherry Creek
    H3: Platt Park
  H2: Frequently Asked Questions About Cold Plunge in Denver
```

---

## 4. URL Structure Standards

### Rules
- All lowercase, hyphens as word separators (no underscores, no spaces)
- No date strings in URLs (they date the content and create update friction)
- No keyword repetition beyond what is natural
- Hierarchy must reflect site architecture (not flat)
- No trailing slash inconsistency — pick one convention and enforce it sitewide

### URL Patterns

| Page Type | Pattern | Example |
|---|---|---|
| Metro hub | `/cold-plunge/[city]/` | `/cold-plunge/denver/` |
| Neighborhood | `/[city]/[keyword-slug]/` | `/denver/cold-plunge-cherry-creek/` |
| Studio detail | `/studio/[studio-slug]/` | `/studio/rok-spas-lodo/` |
| Best-of | `/[city]/best-cold-plunge-[city]/` | `/denver/best-cold-plunge-denver/` |
| Science guide | `/guides/[topic-slug]/` | `/guides/cold-plunge-temperature/` |
| Product review | `/guides/[product-slug]-review/` | `/guides/plunge-cold-plunge-review/` |
| Comparison | `/guides/[a]-vs-[b]/` | `/guides/cold-plunge-vs-ice-bath/` |

### URL Anti-Patterns (flag and fix)
- `/cold-plunge-studios-in-denver-colorado/` — too long, includes stop words
- `/denver-co-cold-plunge/` — geo-abbreviation in URL looks spammy
- `/blog/2024/03/best-cold-plunge/` — date in URL, will need updating
- `/studios/?filter=cold-plunge&city=denver` — dynamic URL, not indexable as intended

---

## 5. Schema Markup Implementation

Schema is not optional — it is a ranking factor for rich results and a trust signal for AI-powered search features (covered in Part 10). Every page type has a required schema set.

### Required Schema by Page Type

| Page Type | Required Schema Types |
|---|---|
| Metro hub | BreadcrumbList, FAQPage, LocalBusiness (aggregate) |
| Neighborhood page | BreadcrumbList, FAQPage |
| Studio detail | LocalBusiness + GeoCoordinates, BreadcrumbList, FAQPage |
| Best-of roundup | ItemList, BreadcrumbList, FAQPage, Article (dateModified) |
| Science guide | Article (dateModified), BreadcrumbList, FAQPage |
| Product review | Review, Product, BreadcrumbList |
| Comparison | Article, BreadcrumbList, FAQPage |

### Validation
- Test every schema implementation with Google's Rich Results Test: https://search.google.com/test/rich-results
- Test BreadcrumbList separately with Schema Markup Validator: https://validator.schema.org/
- Flag any errors or warnings — warnings should be resolved within 1 sprint

### Common Schema Errors to Avoid
- Missing `@context` field
- `LocalBusiness` without `address` (required for Local Pack eligibility)
- `AggregateRating` with fewer than 3 reviews (Google may suppress rich result)
- `FAQPage` with answers over 300 words (Google truncates; target 40–80 words per answer)
- Duplicate `@type` declarations on the same page
- Schema that contradicts visible page content (Google penalizes this)

---

## 6. Core Web Vitals Standards

Google's Core Web Vitals are ranking signals. IceSoak's local directory pages compete primarily in mobile SERPs — mobile performance is the priority.

### Targets

| Metric | Target | Tool to Measure |
|---|---|---|
| LCP (Largest Contentful Paint) | < 2.5 seconds | PageSpeed Insights, CrUX |
| INP (Interaction to Next Paint) | < 200ms | PageSpeed Insights |
| CLS (Cumulative Layout Shift) | < 0.1 | PageSpeed Insights, Lighthouse |

### Common IceSoak Page Issues to Check
- Map embeds (Leaflet): lazy-load the map below the fold; map tiles are a common LCP issue
- Studio listing card images: use WebP format, set explicit width/height attributes to prevent CLS
- Filter UI (modality buttons): ensure filter interactions are debounced to avoid INP spikes
- Third-party scripts (analytics, affiliate tracking): defer non-critical scripts

### Mobile-First Checklist
- [ ] Studio listing cards display cleanly at 375px viewport width
- [ ] Filter buttons are thumb-reachable (min 44px tap target)
- [ ] Map embed doesn't overflow on mobile
- [ ] FAQ accordion opens/closes without layout shift
- [ ] Affiliate CTAs have sufficient tap target size

---

## 7. Image Optimization Standards

### Format
- All images: WebP format (25–35% smaller than JPEG at equivalent quality)
- Fallback: JPEG for browsers that don't support WebP (use `<picture>` element)
- Avoid PNG for photos; use only for logos or images with transparency

### Sizing
- Hero images: 1200 × 630px (also optimal for Open Graph)
- Studio listing card thumbnails: 400 × 300px
- Guide inline images: 800px max width
- Compress all images: target < 80KB for thumbnails, < 200KB for hero images

### Alt Text Standards
- Alt text must describe the image content factually
- Include the studio name or city when relevant
- Do not stuff keywords into alt text
- Wrong: `alt="best cold plunge Denver Colorado ice bath cold water immersion"`
- Right: `alt="ROK SPAS cold plunge tank interior, LoDo Denver"`
- Decorative images: `alt=""`

### File Naming
- Use descriptive, hyphenated filenames
- Wrong: `IMG_4821.jpg`
- Right: `rok-spas-lodo-denver-cold-plunge-tank.webp`

---

## 8. Internal Link Anchor Text Standards

### Rules
- Use descriptive anchor text that tells Google and the user what they'll find at the destination
- Avoid generic anchors: "click here," "learn more," "this page"
- Include the target keyword naturally in the anchor when possible
- Do not use identical anchor text to link to two different pages
- Vary anchor text for links to the same destination (2–3 variations)

### Anchor Text Examples by Link Type

| Link type | Wrong | Right |
|---|---|---|
| Metro hub link | "click here" | "Browse all Denver cold plunge studios" |
| Studio page link | "view listing" | "ROK SPAS LoDo listing" |
| Science guide | "learn more" | "How long should you cold plunge?" |
| Neighborhood page | "see nearby" | "Cold plunge studios near Cherry Creek" |
| Comparison page | "read this" | "Cold plunge vs ice bath — is there a difference?" |

---

## 9. Canonical Tag Rules

### When to Use Canonicals
- Filter pages (e.g., `/cold-plunge/denver/?modality=infrared`) must canonical back to the base page (`/cold-plunge/denver/`)
- Paginated studio list pages: page 2+ canonical to page 1 OR use rel=next/prev
- Mobile-specific URLs (if they exist): canonical to desktop URL
- Any URL with UTM parameters: self-canonical to the clean URL

### Self-Canonical
Every page should include a self-referencing canonical tag:
```html
<link rel="canonical" href="https://icesoak.com/cold-plunge/denver/" />
```
This prevents canonical confusion if the page is discovered via multiple URL paths.

---

## 10. Open Graph and Social Meta Tags

Every page should include Open Graph tags for clean social sharing:

```html
<meta property="og:title" content="[Page Title without | IceSoak suffix]" />
<meta property="og:description" content="[Meta description text]" />
<meta property="og:image" content="https://icesoak.com/images/og/[page-slug]-og.jpg" />
<meta property="og:url" content="https://icesoak.com/[page-path]/" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="IceSoak" />
```

OG image spec: 1200 × 630px, < 300KB, JPG or PNG.

Twitter/X card:
```html
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="[title]" />
<meta name="twitter:description" content="[description]" />
<meta name="twitter:image" content="[image URL]" />
```

---

## 11. Pre-Publish Checklist

Run this checklist on every page before it goes live. Log pass/fail per item.

### Title & Meta
- [ ] Title tag present, 50–60 characters, formula-compliant, unique
- [ ] Meta description present, 140–160 characters, includes CTA, unique
- [ ] OG title, description, and image set

### Headings & Content
- [ ] One H1 only, keyword-matched to title
- [ ] H2s form a logical page outline
- [ ] No H2 or H3 skips in heading hierarchy
- [ ] Word count meets page type target
- [ ] No invented data (all prices, temperatures, ratings from verified sources)
- [ ] IceSoak voice — no hype language, mechanisms cited for benefit claims

### Schema
- [ ] All required schema types present for page type
- [ ] Schema validated with Rich Results Test (no errors)
- [ ] BreadcrumbList matches actual URL path

### Technical
- [ ] Canonical tag set (self-canonical or filter-redirect)
- [ ] No broken internal links (test before publish)
- [ ] Images: WebP format, < 200KB, descriptive alt text, explicit dimensions
- [ ] Page passes Core Web Vitals (LCP < 2.5s, CLS < 0.1) on mobile

### Links
- [ ] Required internal links present (metro hub, guide, neighborhood)
- [ ] Anchor text descriptive and varied
- [ ] External booking/affiliate links use rel="nofollow"
- [ ] FTC disclosure present if affiliate links on page

### Local SEO (city and studio pages only)
- [ ] LocalBusiness schema with complete address and GeoCoordinates
- [ ] Studio name in schema matches Google Business Profile exactly
- [ ] Verification date displayed (within 6 months for "Verified" badge)

---

## Cross-References

- Part 03: Studio Page Optimization (studio-specific schema and content standards)
- Part 04: City Landing Page Strategy (city page templates)
- Part 07: Internal Linking Architecture (anchor text and link placement)
- Part 10: GEO/AI Search Optimization (schema's role in AI search features)

---

*IceSoak SEO Engagement icesoak-jul2026 | Part 06 of 12 | 2026-07-22*
