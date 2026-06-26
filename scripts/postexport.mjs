// Runs after `next build` (static export). Scans the exported `out/` directory,
// excludes any page marked noindex, and writes segmented XML sitemaps plus a
// sitemap index. Source of truth is the real HTML, so the sitemaps can never
// list a page that was guard-railed out.

import { promises as fs } from "node:fs";
import path from "node:path";

const OUT = path.resolve("out");
const BASE = "https://icesoak.com";
const LASTMOD = new Date().toISOString().slice(0, 10);

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (e.name === "_next") continue; // skip framework assets
      files.push(...(await walk(full)));
    } else if (e.name.endsWith(".html")) {
      files.push(full);
    }
  }
  return files;
}

// Map an exported file path to a clean, trailing-slash URL path.
function toUrlPath(file) {
  let rel = path.relative(OUT, file).split(path.sep).join("/");
  if (rel === "index.html") return "/";
  if (rel.endsWith("/index.html")) return "/" + rel.slice(0, -"index.html".length);
  if (rel.endsWith(".html")) return "/" + rel.slice(0, -".html".length) + "/";
  return "/" + rel;
}

function isNoindex(html) {
  const m = html.match(/<meta[^>]+name=["']robots["'][^>]*>/gi);
  if (!m) return false;
  return m.some((tag) => /noindex/i.test(tag));
}

function segmentFor(urlPath) {
  if (urlPath.startsWith("/studio/")) return "studios";
  if (urlPath.startsWith("/guides/")) return "guides";
  return "pages";
}

function urlsetXml(urls) {
  const body = urls
    .map(
      (u) =>
        `  <url>\n    <loc>${BASE}${u}</loc>\n    <lastmod>${LASTMOD}</lastmod>\n  </url>`,
    )
    .join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${body}\n</urlset>\n`;
}

function indexXml(names) {
  const body = names
    .map(
      (n) =>
        `  <sitemap>\n    <loc>${BASE}/${n}</loc>\n    <lastmod>${LASTMOD}</lastmod>\n  </sitemap>`,
    )
    .join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${body}\n</sitemapindex>\n`;
}

async function main() {
  const files = await walk(OUT);
  const segments = new Map(); // name -> string[] of url paths

  for (const file of files) {
    const urlPath = toUrlPath(file);
    const base = path.basename(file);
    if (base === "404.html") continue;
    if (urlPath === "/404/") continue;
    const html = await fs.readFile(file, "utf8");
    if (isNoindex(html)) continue;

    const seg = segmentFor(urlPath);
    if (!segments.has(seg)) segments.set(seg, []);
    segments.get(seg).push(urlPath);
  }

  const sitemapNames = [];
  for (const [seg, urls] of segments) {
    urls.sort();
    const name = `sitemap-${seg}.xml`;
    await fs.writeFile(path.join(OUT, name), urlsetXml(urls), "utf8");
    sitemapNames.push(name);
    console.log(`  sitemap-${seg}.xml: ${urls.length} urls`);
  }
  sitemapNames.sort();

  await fs.writeFile(
    path.join(OUT, "sitemap_index.xml"),
    indexXml(sitemapNames),
    "utf8",
  );

  const total = [...segments.values()].reduce((a, b) => a + b.length, 0);
  console.log(`Sitemaps written: ${sitemapNames.length} segments, ${total} indexable URLs.`);
}

main().catch((err) => {
  console.error("postexport failed:", err);
  process.exit(1);
});
