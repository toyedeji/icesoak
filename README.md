# IceSoak

A cold plunge studio directory for the United States — searchable by
city, with studio details, amenities, pricing, and map pins.
Live at [icesoak.com](https://icesoak.com).

## What It Is

IceSoak helps people find cold plunge and ice bath studios near them.
The directory is built on scraped and curated data, updated weekly via
an automated Python scraper (containerized, orchestrated by n8n in the
reference deployment), and deployed on Netlify with full SEO
groundwork including Google and Bing Search Console verification,
sitemap generation, and IndexNow pinging.

## Architecture

```
┌──────────────────────────┐        ┌───────────────────────────┐
│  Python scraper (weekly) │───────▶│  studios.json (repo root) │
│  podman, Proxmox LXC     │        │  questions.json           │
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

1. `scraper/run_scrape.sh` runs on a weekly cron (orchestrated by n8n
   in the reference deployment, but any cron/scheduler works).
2. The bash wrapper builds a podman image and runs `scrape.py` inside it.
   The scraper crawls source directories, dedupes, and enforces an
   address quality gate (records without a parseable address are dropped).
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
| Scraper | Python (crawl4ai, playwright, httpx) in a podman container |
| Scheduler | Weekly cron (n8n in reference deployment; any scheduler works) |
| Deploy | Netlify |
| DNS | Custom domain (icesoak.com) |
| SEO | Sitemap, robots.txt, Search Console, IndexNow |
| Security | CSP, HSTS, X-Frame-Options, Referrer-Policy headers |

## Features

- City landing pages with filterable studio listings
- Studio detail pages with amenities, pricing, and hours
- Map pins for geocoded studios
- Weekly automated data refresh via a containerized Python scraper
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

The scraper is a Python service (crawl4ai + playwright + httpx) that
runs inside a podman container. `scraper/run_scrape.sh` is the entry
point — it pulls the repo, builds the image, runs `scrape.py` with the
repo root mounted at `/work`, and commits + pushes only if
`studios.json` or `questions.json` changed.

```bash
git clone https://github.com/toyedeji/icesoak /opt/icesoak
cd /opt/icesoak
# Requires podman (or swap to docker in run_scrape.sh) — no host-side
# pip install needed; the container has everything.
bash scraper/run_scrape.sh
```

To schedule weekly runs, add to crontab:

```
0 3 * * 0 /opt/icesoak/scraper/run_scrape.sh >> /var/log/icesoak-scrape.log 2>&1
```

Runs at 03:00 every Sunday. Set `ICESOAK_WORK_DIR` to override the
default `/opt/icesoak` path. In the reference deployment this is
invoked from an n8n workflow rather than plain cron, but the
scheduler is interchangeable — the bash script is the actual work.

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
