# IceSoak

Static directory of cold plunge, sauna, and contrast-therapy studios, built to
rank in Google and be citable by AI answer engines.

## Stack
- **Next.js (App Router) with `output: 'export'`** — every page is fully static
  HTML. No server, no database, no `localStorage`/`sessionStorage`.
- **MapLibre/Leaflet + free OSM tiles** (no API key). The map is the only
  client-side widget; all listing content is server-rendered into the HTML.
- **Netlify** for hosting (see `netlify.toml`).

## Repo layout
- Root — the Next.js static-export app (`app/`, `components/`, `lib/`, `public/`).
- `scraper/` — the Python data pipeline (`scrape.py`, `crawlers/`, `processors/`,
  `utils/`, `Dockerfile`, `run_scrape.sh`, `data/seed_studios.json`).

## Data (single source of truth at the repo root)
- `studios.json` (**repo root**) — array of studios (required: `id, name, metro,
  city, lat, lng, status`; all else nullable). Missing fields are omitted, never
  rendered as `null`. Build succeeds even with stub/empty data. Seeded from
  `scraper/data/seed_studios.json`; the scraper **overwrites this file** on each run.
- `questions.json` (**repo root**) — guide content (15 seeded guides). The scraper
  overwrites this too when its questions crawler produces output.
- `data/metros.json` — metro slug ↔ display name ↔ map center (static site config,
  not scraper output).

## Scraper → site data flow
`scraper/scrape.py` writes `studios.json` and `questions.json` to the **repo root**
(the parent of `scraper/`), which is exactly what the Next.js build imports. Run it
in the container with the repo mounted at `/work`:
```bash
podman run --rm --shm-size=1g -v /opt/icesoak:/work -w /work \
  icesoak-scraper:latest python scraper/scrape.py
# → /opt/icesoak/studios.json and /opt/icesoak/questions.json
```

## Key conventions / decisions
- **`[city]` URL segment = metro slug** (`denver`, `dallas-fort-worth`,
  `philadelphia`). Launch scope is the 3 seeded metros.
- **Indexing guardrail:** a directory page is `index` only when backed by **≥3
  verified studios**; thinner pages render but are `noindex` (kept out of
  sitemaps). Individual studio pages and guides are always indexable.
- With the current seed, the indexable directory pages are **DFW sauna** and
  **DFW infrared sauna**; everything else is noindex until coverage grows. This
  is intentional — it respects the new-domain sandbox and avoids doorway pages.
- The `/cold-plunge/[city]/[neighborhood]` template is **dense-metros-only** and
  is omitted until neighborhood data exists.
- Editorial byline is `IceSoak Editorial` (a real editorial entity) — authorship
  is never fabricated as a fake person.

## SEO / GEO
- Per-page templated `<title>`/meta, one `<h1>`, canonical, breadcrumbs.
- JSON-LD per type: studios → `HealthAndBeautyBusiness` + `BreadcrumbList`;
  guides → `Article` + `FAQPage`; city/list → `ItemList` + `BreadcrumbList`;
  site-wide → `Organization` + `WebSite`.
- `public/robots.txt` allows `GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot,
  Google-Extended` and points at the sitemap index.
- `public/llms.txt` summarizes the site and key sections.
- `scripts/postexport.mjs` scans the exported HTML and writes **segmented
  sitemaps** (`sitemap-pages/guides/studios.xml`) + a **sitemap index**
  (`sitemap_index.xml`), excluding any `noindex` page.

## Commands
```bash
npm install
npm run dev      # local dev
npm run build    # next build (static export to out/) + sitemap generation
npm run start    # serve the built out/ directory locally
```

## Deploy (manual — requires your Netlify auth)
1. `npx netlify deploy --prod` (or connect this repo in the Netlify UI).
2. Point `icesoak.com` at the site; `theicesoak.com` and `www` 301 to it
   (configured in `netlify.toml`).
