// Internal-link maps for the guide <-> city SEO silo.
//
// Every slug here is validated against the live dataset (questions.json /
// metros.json). Where the original SEO brief referenced guides that do not
// exist, the target was remapped to the nearest real guide; targets with no
// reasonable match were dropped. The <InternalLinks> component additionally
// resolves each slug at build time and silently skips anything unresolvable
// (missing guide, or a metro with no directory page), so a stale entry can
// never ship a broken 404 link.
//
// Remaps applied vs. the original brief:
//   cold-plunge-benefits            -> are-cold-plunges-actually-healthy
//   how-long-should-you-cold-plunge -> how-long-should-you-stay-in-a-cold-plunge
//   sauna-benefits                  -> how-often-is-a-sauna-good-for-you
//   sauna-before-or-after-workout   -> (dropped: no equivalent guide exists)
//
// Two link targets live at the top level rather than under /guides/ (see
// TOP_LEVEL_GUIDES): cold-plunge-vs-ice-bath, infrared-vs-traditional-sauna.

// Guide slug -> relevant metro slugs. City links resolve to that metro's
// cold-plunge (or sauna) directory page, whichever exists.
export const GUIDE_TO_CITIES: Record<string, string[]> = {
  // Cold-plunge guides
  "how-often-should-you-do-the-cold-plunge": [
    "denver",
    "dallas-fort-worth",
    "chicago",
    "austin",
    "los-angeles",
    "phoenix",
  ],
  "is-a-3-minute-cold-plunge-safe": [
    "denver",
    "philadelphia",
    "miami",
    "seattle",
    "atlanta",
  ],
  "what-happens-after-30-days-of-ice-baths": [
    "denver",
    "chicago",
    "los-angeles",
    "austin",
    "nashville",
  ],
  "cold-plunge-vs-ice-bath": ["denver", "dallas-fort-worth", "philadelphia", "miami"],
  "are-cold-plunges-actually-healthy": [
    "denver",
    "chicago",
    "los-angeles",
    "austin",
    "seattle",
  ],
  "how-long-should-you-stay-in-a-cold-plunge": [
    "denver",
    "dallas-fort-worth",
    "philadelphia",
    "atlanta",
  ],
  // Sauna guides (city links prefer the sauna directory page)
  "infrared-vs-traditional-sauna": ["denver", "dallas-fort-worth", "chicago", "los-angeles"],
  "how-often-is-a-sauna-good-for-you": ["denver", "philadelphia", "chicago", "nashville"],
};

// Metro slug -> relevant guide slugs shown on that city's directory pages.
export const CITY_TO_GUIDES: Record<string, string[]> = {
  denver: [
    "how-often-should-you-do-the-cold-plunge",
    "cold-plunge-vs-ice-bath",
    "how-often-is-a-sauna-good-for-you",
    "infrared-vs-traditional-sauna",
  ],
  "dallas-fort-worth": [
    "how-long-should-you-stay-in-a-cold-plunge",
    "cold-plunge-vs-ice-bath",
  ],
  philadelphia: [
    "is-a-3-minute-cold-plunge-safe",
    "how-long-should-you-stay-in-a-cold-plunge",
    "how-often-is-a-sauna-good-for-you",
  ],
  chicago: [
    "what-happens-after-30-days-of-ice-baths",
    "are-cold-plunges-actually-healthy",
    "infrared-vs-traditional-sauna",
  ],
  austin: [
    "are-cold-plunges-actually-healthy",
    "what-happens-after-30-days-of-ice-baths",
  ],
  atlanta: [
    "is-a-3-minute-cold-plunge-safe",
    "how-long-should-you-stay-in-a-cold-plunge",
  ],
  seattle: [
    "is-a-3-minute-cold-plunge-safe",
    "are-cold-plunges-actually-healthy",
  ],
  miami: [
    "cold-plunge-vs-ice-bath",
    "how-long-should-you-stay-in-a-cold-plunge",
  ],
  nashville: [
    "how-often-is-a-sauna-good-for-you",
    "what-happens-after-30-days-of-ice-baths",
  ],
  "los-angeles": [
    "are-cold-plunges-actually-healthy",
    "what-happens-after-30-days-of-ice-baths",
  ],
  phoenix: [
    "how-often-should-you-do-the-cold-plunge",
    "are-cold-plunges-actually-healthy",
  ],
};

// Guides that render at the top level (not under /guides/), with display titles.
export const TOP_LEVEL_GUIDES: Record<string, string> = {
  "cold-plunge-vs-ice-bath": "Cold Plunge vs Ice Bath",
  "infrared-vs-traditional-sauna": "Infrared vs Traditional Sauna",
};

// Guides whose city links should prefer the sauna directory page over cold-plunge.
export const SAUNA_GUIDES = new Set<string>([
  "how-often-is-a-sauna-good-for-you",
  "infrared-vs-traditional-sauna",
]);
