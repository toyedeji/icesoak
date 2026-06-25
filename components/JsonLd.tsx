// Renders one or more JSON-LD blocks. Server component → ships in static HTML,
// so AI answer engines and crawlers see structured data without running JS.
export default function JsonLd({ data }: { data: unknown | unknown[] }) {
  const blocks = Array.isArray(data) ? data.filter(Boolean) : [data].filter(Boolean);
  return (
    <>
      {blocks.map((block, i) => (
        <script
          key={i}
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(block) }}
        />
      ))}
    </>
  );
}
