// Post-build gate. Runs after `next build` and scripts/postexport.mjs, and a
// failure here fails the Netlify deploy.
//
// Everything below asserts against the EXPORTED HTML in out/, never against
// questions.json or component source. That distinction is the whole point: a
// grep over source would pass while the template that consumes it was broken,
// and the failure mode being guarded — a $4,990 cold plunge tub at the bottom
// of a page about autoimmune thyroid disease — is invisible in the data layer.
//
// Deliberately NOT here: the two known-failing assertions in lib/*.test.ts
// (placeholder disclaimer copy, unverified corrections mailbox). Those are open
// editorial items, and wiring them into the deploy gate would block the entire
// remediation from shipping over copy that has not been written yet.
import { promises as fs } from "node:fs";
import path from "node:path";

const OUT = path.resolve("out");
const ROOT = path.resolve(".");

const failures = [];
const checks = [];

function check(name, ok, detail = "") {
  checks.push({ name, ok });
  if (!ok) failures.push(detail ? `${name}\n      ${detail}` : name);
}

async function read(rel) {
  try {
    return await fs.readFile(path.join(OUT, rel), "utf8");
  } catch {
    return null;
  }
}

const exists = async (rel) => (await read(rel)) !== null;

// The affiliate block's own heading and the sponsored links it wraps. Matching
// both means a partial render (heading kept, cards dropped, or vice versa)
// still trips the gate.
const AFFILIATE_MARKERS = [">Practice at Home<", 'rel="sponsored'];
const hasAffiliate = (html) => AFFILIATE_MARKERS.some((m) => html.includes(m));
const hasDisclaimer = (html) => html.includes('aria-label="Medical disclaimer"');

const guidePath = (slug) => `guides/${slug}/index.html`;

// ---------------------------------------------------------------------------
// 1. The named pages from the audit.
// ---------------------------------------------------------------------------
for (const slug of ["does-sauna-help-hashimotos", "is-a-40-degree-ice-bath-safe"]) {
  const html = await read(guidePath(slug));
  check(`${slug} renders`, html !== null, `missing ${guidePath(slug)}`);
  if (html) {
    check(
      `${slug} has NO affiliate block`,
      !hasAffiliate(html),
      "the Practice at Home block is rendering on a suppressed page",
    );
    check(`${slug} has a medical disclaimer`, hasDisclaimer(html));
  }
}

{
  const slug = "what-is-the-average-cost-of-a-cold-plunge";
  const html = await read(guidePath(slug));
  check(`${slug} renders`, html !== null, `missing ${guidePath(slug)}`);
  if (html) {
    check(
      `${slug} DOES have an affiliate block`,
      hasAffiliate(html),
      "the gate has become a blanket kill switch instead of a topical one",
    );
  }
}

// ---------------------------------------------------------------------------
// 2. Every published guide, not just the three named ones. Tier is read back
//    out of questions.json but VERIFIED against the rendered page.
// ---------------------------------------------------------------------------
const questions = JSON.parse(await fs.readFile(path.join(ROOT, "questions.json"), "utf8"));
const published = questions.filter((q) =>
  (q.sections ?? []).some((s) => s?.body?.trim()),
);

let suppressed = 0;
let monetized = 0;
for (const q of published) {
  const html = await read(guidePath(q.slug));
  if (html === null) {
    check(`${q.slug} renders`, false, `published guide has no ${guidePath(q.slug)}`);
    continue;
  }
  const shouldSell = ["C", "D", "E"].includes(q.risk_tier);
  const shouldWarn = ["A", "B"].includes(q.risk_tier);
  shouldSell ? monetized++ : suppressed++;

  check(
    `tier ${q.risk_tier} ${q.slug}: affiliate block ${shouldSell ? "present" : "absent"}`,
    hasAffiliate(html) === shouldSell,
    `risk_tier ${q.risk_tier} but affiliate block is ${hasAffiliate(html) ? "PRESENT" : "absent"}`,
  );
  check(
    `tier ${q.risk_tier} ${q.slug}: disclaimer ${shouldWarn ? "present" : "absent"}`,
    hasDisclaimer(html) === shouldWarn,
    `risk_tier ${q.risk_tier} but disclaimer is ${hasDisclaimer(html) ? "PRESENT" : "absent"}`,
  );
  check(
    `${q.slug} byline says it is not medically reviewed`,
    html.includes("Not medically reviewed"),
  );
  check(
    `${q.slug} no longer claims an editorial body`,
    !html.includes("IceSoak Editorial"),
  );
}

// ---------------------------------------------------------------------------
// 3. The seven removals: 301, not 404. In a static export that means the file
//    must NOT exist (an existing file shadows a force = false redirect and the
//    URL would answer 200) and netlify.toml must carry the rule.
// ---------------------------------------------------------------------------
const denylist = JSON.parse(
  await fs.readFile(path.join(ROOT, "guide_denylist.json"), "utf8"),
).slugs;
const toml = await fs.readFile(path.join(ROOT, "netlify.toml"), "utf8");

const rules = [...toml.matchAll(/\[\[redirects\]\]([\s\S]*?)(?=\n\s*\[|\s*$)/g)].map((m) => {
  const body = m[1];
  const field = (k) => body.match(new RegExp(`${k}\\s*=\\s*"([^"]*)"`))?.[1];
  return {
    from: field("from"),
    to: field("to"),
    status: body.match(/status\s*=\s*(\d+)/)?.[1],
    force: /force\s*=\s*true/.test(body),
  };
});

for (const [slug, meta] of Object.entries(denylist)) {
  const from = `/guides/${slug}/`;

  check(
    `${slug} emits no static page`,
    !(await exists(guidePath(slug))),
    `out/${guidePath(slug)} exists — it will be served 200 and shadow the 301`,
  );

  const rule = rules.find((r) => r.from === from);
  check(`${slug} has a redirect rule`, Boolean(rule), `no [[redirects]] with from = "${from}"`);
  if (rule) {
    check(`${slug} redirects 301`, rule.status === "301", `status = ${rule.status}`);
    check(`${slug} redirect target matches the denylist`, rule.to === meta.redirect_to,
      `netlify.toml says ${rule.to}, guide_denylist.json says ${meta.redirect_to}`);

    // Single hop: the target must be a real page in this build, not another
    // redirect. A chain loses more signal than it saves.
    const targetFile = rule.to.replace(/^\//, "").replace(/\/$/, "") + "/index.html";
    check(
      `${slug} target ${rule.to} returns 200`,
      await exists(targetFile),
      `out/${targetFile} does not exist — the redirect lands on a 404`,
    );
    check(
      `${slug} target is not itself redirected`,
      !rules.some((r) => r.from === rule.to),
      `${rule.to} has its own redirect rule — that is a two-hop chain`,
    );
  }
}

// ---------------------------------------------------------------------------
// 4. Sitemap. postexport.mjs derives it from rendered robots tags, so this
//    catches a guide that silently went noindex as well as a bad count.
// ---------------------------------------------------------------------------
const sitemap = await read("sitemap-guides.xml");
check("sitemap-guides.xml exists", sitemap !== null);
if (sitemap) {
  const locs = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
  // published guides + the /guides/ index page itself
  check(
    `sitemap lists ${published.length + 1} guide URLs`,
    locs.length === published.length + 1,
    `expected ${published.length + 1}, got ${locs.length}`,
  );
  for (const slug of Object.keys(denylist)) {
    check(
      `sitemap excludes ${slug}`,
      !locs.some((l) => l.includes(`/guides/${slug}/`)),
    );
  }
}

// ---------------------------------------------------------------------------
// 5. The editorial standards page the bylines and disclaimers link to.
// ---------------------------------------------------------------------------
check("/editorial-standards/ returns 200", await exists("editorial-standards/index.html"));

// ---------------------------------------------------------------------------
const passed = checks.length - failures.length;
if (failures.length) {
  console.error(
    `\n[icesoak] BUILD GATE FAILED — ${failures.length}/${checks.length} assertions\n\n  ` +
      failures.map((f) => `✗ ${f}`).join("\n  ") +
      "\n",
  );
  process.exit(1);
}
console.log(
  `[icesoak] build gate: ${passed}/${checks.length} assertions passed ` +
    `(${published.length} published guides — ${suppressed} affiliate-suppressed, ` +
    `${monetized} monetized; ${Object.keys(denylist).length} removals verified 301)`,
);
