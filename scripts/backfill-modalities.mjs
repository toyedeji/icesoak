// One-time backfill: infer modality tags from studio name text for records
// with an empty modalities array. Keyword-only — no default/fallback tag, so
// studios with no matching keyword stay untagged (accuracy over coverage).
//
// Tag vocabulary matches the predicates in lib/studios.ts exactly:
//   cold_plunge, sauna, sauna_infrared
// "contrast" is not a stored tag — hasContrast() derives it from the
// presence of both a cold tag and a sauna-type tag on the same studio.

import { promises as fs } from "node:fs";

const PATH = "studios.json";

const RULES = [
  { re: /cold plunge|ice bath/i, tag: "cold_plunge" },
  { re: /infrared/i, tag: "sauna_infrared" },
  { re: /sauna/i, tag: "sauna" },
];

async function main() {
  const raw = await fs.readFile(PATH, "utf8");
  const studios = JSON.parse(raw);

  let matched = 0;
  let untouched = 0;
  const matchedNames = [];

  for (const s of studios) {
    const current = Array.isArray(s.modalities) ? s.modalities : [];
    if (current.length > 0) continue;

    const tags = new Set();
    for (const { re, tag } of RULES) {
      if (re.test(s.name)) tags.add(tag);
    }

    if (tags.size > 0) {
      s.modalities = [...tags];
      matched++;
      matchedNames.push({ name: s.name, tags: [...tags] });
    } else {
      untouched++;
    }
  }

  await fs.writeFile(PATH, JSON.stringify(studios, null, 2) + "\n", "utf8");

  console.log(`Backfilled ${matched} studios from name-keyword match.`);
  console.log(`${untouched} studios left untouched (no keyword match, still empty).`);
  console.log(JSON.stringify(matchedNames, null, 2));
}

main();
