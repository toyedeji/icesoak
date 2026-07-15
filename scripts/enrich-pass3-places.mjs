// Pass 3: infer modality tags for studios still untagged after the
// name-keyword backfill (scripts/backfill-modalities.mjs) and franchise
// brand map (scripts/enrich-pass1-franchise.mjs), using the Google Places
// API (New) — searchText to locate the place, keyword-scanning its
// name/types/editorial summary.
//
// Tag vocabulary matches the predicates in lib/studios.ts exactly:
//   cold_plunge, sauna, sauna_infrared
// "contrast" is not a stored tag — hasContrast() derives it from the
// presence of both a cold tag and a sauna-type tag on the same studio.

import { promises as fs } from "node:fs";

const PATH = "studios.json";
const API_KEY = process.env.GOOGLE_PLACES_API_KEY;
const SEARCH_URL = "https://places.googleapis.com/v1/places:searchText";
const SLEEP_MS = 200;

if (!API_KEY) {
  console.error("GOOGLE_PLACES_API_KEY is not set.");
  process.exit(1);
}

const RULES = [
  { re: /cold plunge|ice bath|cold immersion/i, tag: "cold_plunge" },
  { re: /infrared/i, tag: "sauna_infrared" },
  { re: /sauna|steam|banya|nordic|sweat|heat therapy|contrast/i, tag: "sauna" },
];

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function searchPlace(query) {
  const res = await fetch(SEARCH_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Goog-Api-Key": API_KEY,
      "X-Goog-FieldMask": "places.displayName,places.types,places.editorialSummary",
    },
    body: JSON.stringify({ textQuery: query }),
  });

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  }

  const data = await res.json();
  return data.places?.[0] ?? null;
}

function inferTags(place) {
  const haystack = [
    place.displayName?.text ?? "",
    ...(place.types ?? []),
    place.editorialSummary?.text ?? "",
  ]
    .join(" ")
    .replace(/_/g, " ");

  const tags = new Set();
  for (const { re, tag } of RULES) {
    if (re.test(haystack)) tags.add(tag);
  }
  // sauna_infrared implies sauna
  if (tags.has("sauna_infrared")) tags.add("sauna");

  return [...tags];
}

async function main() {
  const raw = await fs.readFile(PATH, "utf8");
  const studios = JSON.parse(raw);

  const untagged = studios.filter(
    (s) => !Array.isArray(s.modalities) || s.modalities.length === 0
  );

  let tagged = 0;
  let noTags = 0;
  let failed = 0;
  const stillUntagged = [];

  for (const s of untagged) {
    const query = `${s.name} ${s.address ?? ""}`.trim();
    try {
      const place = await searchPlace(query);
      if (!place) {
        noTags++;
        stillUntagged.push(s.name);
        await sleep(SLEEP_MS);
        continue;
      }

      const tags = inferTags(place);
      if (tags.length > 0) {
        s.modalities = tags;
        tagged++;
        console.log(`TAGGED  ${s.name} -> ${tags.join(", ")}`);
      } else {
        noTags++;
        stillUntagged.push(s.name);
        console.log(`NO TAGS ${s.name}`);
      }
    } catch (err) {
      failed++;
      stillUntagged.push(s.name);
      console.log(`FAILED  ${s.name} -> ${err.message}`);
    }

    await sleep(SLEEP_MS);
  }

  await fs.writeFile(PATH, JSON.stringify(studios, null, 2) + "\n", "utf8");

  const finalTagged = studios.filter(
    (s) => Array.isArray(s.modalities) && s.modalities.length > 0
  ).length;

  console.log("\n=== Pass 3 summary ===");
  console.log(`tagged:   ${tagged}`);
  console.log(`no_tags:  ${noTags}`);
  console.log(`failed:   ${failed}`);
  console.log(`Final coverage: ${finalTagged}/${studios.length}`);
  console.log(`Still untagged (${stillUntagged.length}):`);
  stillUntagged.forEach((name) => console.log(`  - ${name}`));
}

main();
