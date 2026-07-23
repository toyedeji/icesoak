# IceSoak — Cold Plunge Metro Title/Meta Audit

- **Date:** 2026-07-22
- **Repo:** github.com/toyedeji/icesoak (branch `main`)
- **Route audited:** `app/cold-plunge/[city]/` (dynamic route — titles/meta are template-generated in `lib/verticalPage.tsx` → `verticalMetadata()`, using `lib/copy.ts` `cityDescription()` and `lib/seo.ts` `clamp()`)
- **Cities generated:** 11 (every metro in `data/metros.json` with ≥1 `cold_plunge` studio; metros with 0 qualifying studios 404 and are not generated)

## Method / how each string is built

- **Rendered `<title>`** = `Cold Plunge Studios in {City}, {State}` + ` | IceSoak` (the ` | IceSoak` suffix is applied site-wide by the root layout title template in `app/layout.tsx`). Char counts below are of the **full rendered title tag** — what Google actually displays. (The base title without brand is 32–44 chars; the base fails 50–60 even more clearly, so the conclusion is identical either way.)
- **Meta description** = `clamp(cityDescription(...), 158)`. For populated metros the template is: `Find and compare {n} verified cold plunge studios in {City}, {State}. Browse locations, modalities, and nearby options on IceSoak.` — always well under the 158 clamp, so no truncation occurs.

## Rules applied

- **Title:** 50–60 chars; must include city name + "cold plunge" + "studios".
- **Meta:** 150–160 chars; must include city name; must end with a CTA.

## Result summary

| Check | Passing | Failing |
|---|---|---|
| Title length (50–60) | 1 / 11 (Dallas–Fort Worth only) | 10 / 11 |
| Title keywords (city + cold plunge + studios) | 11 / 11 | 0 |
| Meta length (150–160) | 0 / 11 | 11 / 11 |
| Meta city + CTA | 11 / 11 | 0 |
| **Pass BOTH title & meta** | **0 / 11** | **11 / 11** |

**Root cause:** both failures are purely **length** — the shared template produces titles that are too short (all but DFW under 50) and meta descriptions ~25–35 chars too short (122–135 vs. the 150 floor). Every page already contains the required keywords, city name, and a CTA. This is a **single template fix**, not 11 separate content edits.

## Audit table

| City | Title (chars) | Meta (chars) | Title Pass | Meta Pass | Suggested Fix |
|---|---|---|---|---|---|
| Atlanta, GA | `Cold Plunge Studios in Atlanta, GA \| IceSoak` (44) | 125 | ❌ (too short) | ❌ (too short) | **Title (52):** `12 Best Cold Plunge Studios in Atlanta, GA \| IceSoak` · **Meta (152):** `Compare 12 verified cold plunge studios in Atlanta, GA. Browse locations, modalities, day passes, and Google ratings, then book your session on IceSoak.` |
| Austin, TX | `Cold Plunge Studios in Austin, TX \| IceSoak` (43) | 124 | ❌ (too short) | ❌ (too short) | **Title (51):** `10 Best Cold Plunge Studios in Austin, TX \| IceSoak` · **Meta (151):** `Compare 10 verified cold plunge studios in Austin, TX. Browse locations, modalities, day passes, and Google ratings, then book your session on IceSoak.` |
| Chicago, IL | `Cold Plunge Studios in Chicago, IL \| IceSoak` (44) | 125 | ❌ (too short) | ❌ (too short) | **Title (52):** `10 Best Cold Plunge Studios in Chicago, IL \| IceSoak` · **Meta (152):** `Compare 10 verified cold plunge studios in Chicago, IL. Browse locations, modalities, day passes, and Google ratings, then book your session on IceSoak.` |
| Dallas–Fort Worth, TX | `Cold Plunge Studios in Dallas–Fort Worth, TX \| IceSoak` (54) | 135 | ✅ | ❌ (too short) | **Title:** already passes (54) · **Meta (158):** `Find and compare 20 verified cold plunge studios in Dallas–Fort Worth, TX. Browse locations, modalities, and day-pass pricing, then book your soak on IceSoak.` |
| Denver, CO | `Cold Plunge Studios in Denver, CO \| IceSoak` (43) | 124 | ❌ (too short) | ❌ (too short) | **Title (51):** `17 Best Cold Plunge Studios in Denver, CO \| IceSoak` · **Meta (151):** `Compare 17 verified cold plunge studios in Denver, CO. Browse locations, modalities, day passes, and Google ratings, then book your session on IceSoak.` |
| Los Angeles, CA | `Cold Plunge Studios in Los Angeles, CA \| IceSoak` (48) | 128 | ❌ (too short) | ❌ (too short) | **Title (53):** `Best Cold Plunge Studios in Los Angeles, CA \| IceSoak` · **Meta (151):** `Find and compare 7 verified cold plunge studios in Los Angeles, CA. Browse locations, modalities, and day-pass pricing, then book your soak on IceSoak.` |
| Miami, FL | `Cold Plunge Studios in Miami, FL \| IceSoak` (42) | 122 | ❌ (too short) | ❌ (too short) | **Title (55):** `Cold Plunge Studios in Miami, FL (9 Verified) \| IceSoak` · **Meta (151):** `Find and compare 9 verified cold plunge studios in Miami, FL. Browse locations, modalities, day passes, and ratings, then book your session on IceSoak.` |
| Nashville, TN | `Cold Plunge Studios in Nashville, TN \| IceSoak` (46) | 127 | ❌ (too short) | ❌ (too short) | **Title (51):** `Best Cold Plunge Studios in Nashville, TN \| IceSoak` · **Meta (150):** `Find and compare 17 verified cold plunge studios in Nashville, TN. Browse locations, modalities, and day-pass pricing, then book your soak on IceSoak.` |
| Philadelphia, PA | `Cold Plunge Studios in Philadelphia, PA \| IceSoak` (49) | 130 | ❌ (too short) | ❌ (too short) | **Title (54):** `Best Cold Plunge Studios in Philadelphia, PA \| IceSoak` · **Meta (153):** `Find and compare 17 verified cold plunge studios in Philadelphia, PA. Browse locations, modalities, and day-pass pricing, then book your soak on IceSoak.` |
| Phoenix, AZ | `Cold Plunge Studios in Phoenix, AZ \| IceSoak` (44) | 124 | ❌ (too short) | ❌ (too short) | **Title (51):** `5 Best Cold Plunge Studios in Phoenix, AZ \| IceSoak` · **Meta (151):** `Compare 5 verified cold plunge studios in Phoenix, AZ. Browse locations, modalities, day passes, and Google ratings, then book your session on IceSoak.` |
| Seattle, WA | `Cold Plunge Studios in Seattle, WA \| IceSoak` (44) | 124 | ❌ (too short) | ❌ (too short) | **Title (51):** `6 Best Cold Plunge Studios in Seattle, WA \| IceSoak` · **Meta (151):** `Compare 6 verified cold plunge studios in Seattle, WA. Browse locations, modalities, day passes, and Google ratings, then book your session on IceSoak.` |

All suggested titles are 50–60 chars and all suggested metas are 150–160 chars, each retaining city name + "cold plunge" + "studios" and ending on a CTA (verified programmatically).

## Recommended batch fix (11 pages > 5 → not committed this run)

Per the task rule, changes were **not committed** because 11 pages need edits (threshold is ≤5). Because the pages are template-generated, the correct remediation is **two shared code edits**, which fixes all 11 (and keeps future metros compliant automatically):

1. **`lib/verticalPage.tsx` → `verticalMetadata()`** — lengthen the title template. Add a count and/or a "Best" qualifier so the rendered tag lands 50–60, e.g. `` `${studios.length} Best ${label} Studios in ${metro.name}, ${metro.state}` `` (verify per-metro length; long metro names like Dallas–Fort Worth may need the plain form to avoid exceeding 60).
2. **`lib/copy.ts` → `cityDescription()`** — extend the populated-metro description to ~150–160 chars ending in a CTA, e.g. `` `Find and compare ${n} verified cold plunge studios in ${metro.name}, ${metro.state}. Browse locations, modalities, and day-pass pricing, then book your session on IceSoak.` `` (the same rewrite naturally benefits sauna / infrared-sauna / contrast-therapy verticals, whose nouns differ — confirm their lengths too).

> ⚠️ Because titles/meta are computed from `studios.length`, the exact char count shifts as the studio count changes (single vs. double digit). Any template must be re-validated across all metros after editing — the per-city strings above are the target outputs to match.

## Task 1 note (robots.txt)

`public/robots.txt` already explicitly allows `GPTBot`, `PerplexityBot`, and `ClaudeBot` (plus OAI-SearchBot, ChatGPT-User, Claude-Web, Google-Extended). `Googlebot` is allowed via `User-agent: *` → `Allow: /`. No changes required; nothing committed.
