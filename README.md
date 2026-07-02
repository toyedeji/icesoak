# IceSoak

A cold plunge studio directory for the United States — searchable by
city, with studio details, amenities, pricing, and map pins.
Live at [icesoak.com](https://icesoak.com).

## What It Is

IceSoak helps people find cold plunge and ice bath studios near them.
The directory is built on scraped and curated data, updated weekly via
an automated n8n pipeline, and deployed on Netlify with full SEO
groundwork including Google and Bing Search Console verification,
sitemap generation, and IndexNow pinging.

## Architecture

```
┌──────────────────────────┐        ┌───────────────────────────┐
│  n8n scraper (weekly)    │───────▶│  studios.json (repo root) │
│  self-hosted Proxmox LXC │        │  questions.json           │
└──────────────────────────┘        └────────────┬──────────────┘
                                                  │
                                                  ▼
                                    ┌────────────────────────────┐
                                    │  Next.js static export     │
                                    │  App Router + output: export│
                                    └────────────┬───────────────┘
                                                  │
                                                  ▼
                                    ┌────────────────────────────┐
                                    │  Netlify → icesoak.com     │
                                    │  segmented sitemap,        │
                                    │  IndexNow ping on updates  │
                                    └────────────────────────────┘
```

Data flow:

1. n8n workflow runs on a weekly cron.
2. Scraper crawls source directories, dedupes, and enforces an address
   quality gate (records without a parseable address are dropped).
3. Output is written to `studios.json` and `questions.json` at the
   repo root — the single source of truth the Next.js build imports.
4. Push to `main` triggers a Netlify build.
5. `scripts/postexport.mjs` scans the exported HTML and writes a
   segmented sitemap index (pages / guides / studios), excluding
   `noindex` pages.
6. IndexNow pings Bing on updates for near-instant indexing.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (TypeScript) |
| Styling | Tailwind CSS |
| Scraper | n8n (self-hosted, Proxmox LXC) |
| Deploy | Netlify |
| DNS | Custom domain (icesoak.com) |
| SEO | Sitemap, robots.txt, Search Console, IndexNow |
| Security | CSP, HSTS, X-Frame-Options, Referrer-Policy headers |

## Features

- City landing pages with filterable studio listings
- Studio detail pages with amenities, pricing, and hours
- Map pins for geocoded studios
- Weekly automated data refresh via n8n scraper
- Address parsing with quality gate (filters incomplete records)
- Mobile-responsive layout
- Enterprise-grade security headers

## SEO Architecture

Each city gets a dedicated landing page optimized for
`cold plunge studios in <city>` and related queries.
Studio slugs are human-readable and stable.
Sitemap submitted to both Google and Bing Search Console.
IndexNow key registered for instant Bing indexing on updates.

## Self-Hosting the Scraper

The n8n scraper workflow runs on a self-hosted Proxmox LXC container
on a weekly schedule. To run your own:

1. Install [n8n](https://n8n.io) (self-hosted or cloud)
2. Import the workflow from `/scraper/`
3. Configure your data output path
4. Set a weekly cron trigger

## Local Development

```bash
git clone https://github.com/toyedeji/icesoak
cd icesoak
npm install
npm run dev
# Visit http://localhost:3000
```

## Deployment

Deployed via Netlify with automatic builds on push to main.

```bash
# Manual deploy via Netlify CLI
netlify deploy --prod
```

## Project Status

- ✅ Live at icesoak.com
- ✅ ~141 studios scraped across multiple cities
- ✅ Google + Bing Search Console verified
- ✅ Sitemap indexed
- ⏳ Geocoding lat/lng for all studios (map pins)
- ⏳ City expansion (gated on Search Console data)
- ⏳ Affiliate program integrations
