#!/usr/bin/env node
/**
 * Pass 1 — Franchise brand-map enrichment.
 *
 * Many untagged studios are known franchise brands with consistent modalities.
 * This tags any studio that STILL has empty modalities by matching its name
 * against a brand->modalities map.
 *
 * Tokens are CANONICAL (match scraper/utils/schema.py + the frontend in
 * lib/format.ts / lib/studios.ts): cold_plunge, sauna, sauna_infrared,
 * sauna_traditional, contrast, cryo. (The source prompt used the non-existent
 * tokens "contrast_therapy"/"cryotherapy"; those are normalized here so the
 * tagged studios actually surface on the site's filters and SEO facet pages.)
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const STUDIOS_PATH = join(__dirname, "..", "studios.json");

// Map non-canonical labels from the source prompt to the tokens the codebase
// actually uses. Everything else passes through unchanged.
const TOKEN_ALIASES = {
  cryotherapy: "cryo",
  contrast_therapy: "contrast",
};
const canon = (mods) => mods.map((m) => TOKEN_ALIASES[m] ?? m);

const FRANCHISE_MODALITIES = {
  // Sauna + cold plunge franchise chains
  "sweathouz":        ["sauna_infrared", "cold_plunge", "contrast"],
  "swthz":            ["sauna_infrared", "cold_plunge", "contrast"],
  "perspire sauna":   ["sauna_infrared"],
  "pure sweat":       ["sauna_infrared", "cold_plunge"],
  "urban sweat":      ["sauna_infrared", "cold_plunge"],
  "glow sauna":       ["sauna_infrared"],
  "pause studio":     ["sauna_infrared", "cold_plunge", "contrast"],
  "pause venice":     ["sauna_infrared", "cold_plunge"],
  "city sweats":      ["sauna_infrared", "cold_plunge", "contrast"],
  "sauna house":      ["sauna_traditional", "cold_plunge"],
  "bywater sauna":    ["sauna_traditional"],
  "hothouse spa":     ["sauna_traditional", "cold_plunge"],
  "naosu":            ["sauna_infrared"],
  "ritual community": ["sauna_traditional"],
  "seek sauna":       ["sauna_infrared"],
  "sek sauna":        ["sauna_infrared"],
  "contrast studio":  ["sauna_infrared", "cold_plunge", "contrast"],
  "formation sauna":  ["sauna_infrared", "cold_plunge"],
  "surge sauna":      ["sauna_infrared", "cold_plunge", "contrast"],
  "dtxfy":            ["sauna_infrared"],
  "elev8 infrared":   ["sauna_infrared"],
  "sweatheory":       ["sauna_infrared"],
  "r3 experience":    ["cold_plunge", "cryo"],
  "r3 spa":           ["cold_plunge", "sauna_infrared"],
  "r3 cryo":          ["cryo", "cold_plunge"],
  "icebox cryo":      ["cryo", "cold_plunge"],
  "icebox":           ["cryo", "cold_plunge"],
  "cryobar":          ["cryo"],
  "cryohealthcare":   ["cryo", "cold_plunge"],
  "cryo tempe":       ["cryo"],
  "cryo miami":       ["cryo"],
  "cryo boost":       ["cryo"],
  "icryo":            ["cryo"],
  "orange cryo":      ["cryo"],
  "restore hyper":    ["cold_plunge", "cryo", "contrast"],
  "restore hy":       ["cold_plunge", "cryo"],
  "beem light":       ["sauna_infrared"],
  "campfire sauna":   ["sauna_traditional"],
  "oak st. sauna":    ["sauna_traditional"],
  "riverwalk sauna":  ["sauna_traditional"],
  "vihta sauna":      ["sauna_traditional"],
  "von sauna":        ["sauna_traditional"],
  "salt & cedar":     ["sauna_traditional"],
  "sauna hut":        ["sauna_traditional"],
  "sauna sanctuary":  ["sauna_traditional"],
  "sunsauna":         ["sauna_infrared"],
  "fyre sauna":       ["sauna_infrared"],
  "wild haus":        ["sauna_traditional"],
  "icepass":          ["cold_plunge", "sauna"],
  "westside sweat":   ["sauna_infrared", "cold_plunge"],
  "melt well":        ["sauna_infrared", "cold_plunge"],
  "optimal health":   ["sauna_infrared"],
  "eleos float":      ["sauna_infrared", "cold_plunge"],
  "flow state cryo":  ["cryo", "cold_plunge"],
  "livecolder":       ["cold_plunge"],
  "subzero plunge":   ["cold_plunge"],
  "cold plunge austin": ["cold_plunge"],
  "cold plunge philly": ["cold_plunge"],
  "ocean lab":        ["cold_plunge", "contrast"],
  "ulu recovery":     ["cold_plunge", "sauna"],
  "pure recovery":    ["cold_plunge", "cryo"],
  "king spa":         ["sauna_traditional", "cold_plunge"],
  "polar star":       ["sauna_traditional", "cold_plunge"],
  "chicago sweatlodge": ["sauna_traditional"],
  "contrast hot":     ["cold_plunge", "sauna", "contrast"],
  "fire and ice":     ["sauna", "cold_plunge", "contrast"],
  "warriors garden":  ["cold_plunge", "sauna"],
  "warrior garden":   ["cold_plunge", "sauna"],
  "aura sauna":       ["sauna_infrared"],
  "sauna phl":        ["sauna_infrared"],
  "sauna moon":       ["sauna_traditional"],
  "crockpot sauna":   ["sauna_traditional"],
  "halsa nordic":     ["sauna_traditional"],
  "portal":           ["sauna_traditional", "cold_plunge", "contrast"],
  "therma haus":      ["sauna", "cold_plunge", "contrast"],
  "havana sauna":     ["sauna_traditional"],
  "simply sauna":     ["sauna_infrared"],
  "apres sauna":      ["sauna_infrared"],
  "dear sauna":       ["sauna_traditional"],
  "sauna room":       ["sauna_infrared"],
  "sauna to-go":      ["sauna_traditional"],
  "nomadic fire":     ["sauna_traditional"],
  "peak recovery":    ["cold_plunge", "sauna"],
  "urban unwind":     ["sauna_infrared"],
  "sweat shack":      ["sauna_infrared", "cold_plunge"],
  "contrast club":    ["sauna", "cold_plunge", "contrast"],
  "sweat plunge":     ["sauna", "cold_plunge", "contrast"],
  "rok spas":         ["sauna", "cold_plunge"],
  "naos":             ["cold_plunge"],
  "blue recovery":    ["cold_plunge", "sauna"],
  "ice room":         ["cold_plunge"],
  "recovery lounge":  ["cold_plunge", "sauna"],
  "recovery space":   ["cold_plunge"],
  "recovery studio":  ["cold_plunge", "sauna"],
  "nexus recovery lab": ["cold_plunge", "cryo"],
  "helix performance": ["cold_plunge", "cryo"],
  "electric ice":     ["cryo", "cold_plunge"],
  "rivera performance": ["cold_plunge"],
  "royal standard":   ["sauna"],
  "five star sauna":  ["sauna_infrared"],
  "infrared sauna store": ["sauna_infrared"],
  "miami infrared":   ["sauna_infrared"],
  "cloud nine":       ["sauna_infrared", "cold_plunge"],
  "polar star spa":   ["sauna_traditional", "cold_plunge"],
  "hothouse":         ["sauna_traditional", "cold_plunge"],
  "seattle sauna":    ["sauna_traditional"],
  "dtxfy infrared":   ["sauna_infrared"],
};

// Precompute keys longest-first so the most specific brand wins.
const KEYS_BY_LENGTH = Object.keys(FRANCHISE_MODALITIES).sort(
  (a, b) => b.length - a.length,
);
const MIN_KEY_LEN = 5; // avoid false matches from short/generic keys

function matchBrand(name) {
  const low = name.toLowerCase();
  for (const key of KEYS_BY_LENGTH) {
    if (key.length >= MIN_KEY_LEN && low.includes(key)) {
      return { key, modalities: canon(FRANCHISE_MODALITIES[key]) };
    }
  }
  return null;
}

function main() {
  const studios = JSON.parse(readFileSync(STUDIOS_PATH, "utf-8"));

  const tagged = [];
  for (const s of studios) {
    // Never overwrite existing modalities.
    if (Array.isArray(s.modalities) && s.modalities.length > 0) continue;

    const hit = matchBrand(s.name || "");
    if (!hit) continue;

    s.modalities = hit.modalities;
    tagged.push({ name: s.name, metro: s.metro, key: hit.key, modalities: hit.modalities });
  }

  writeFileSync(STUDIOS_PATH, JSON.stringify(studios, null, 2) + "\n");

  const stillEmpty = studios.filter(
    (x) => !Array.isArray(x.modalities) || x.modalities.length === 0,
  );

  console.log(`Pass 1 (franchise brand map): tagged ${tagged.length} studios\n`);
  for (const t of tagged) {
    console.log(`  ${t.name}  [${t.metro}]  (matched "${t.key}") -> [${t.modalities.join(", ")}]`);
  }
  console.log(`\nStill empty after Pass 1: ${stillEmpty.length}`);
}

main();
