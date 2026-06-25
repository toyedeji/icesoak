import Link from "next/link";
import type { Crumb } from "@/lib/jsonld";

// Visible breadcrumb trail. The matching BreadcrumbList JSON-LD is emitted
// separately by each page so the markup and structured data stay in sync.
export default function Breadcrumbs({ crumbs }: { crumbs: Crumb[] }) {
  return (
    <nav aria-label="Breadcrumb" className="breadcrumbs">
      <ol>
        {crumbs.map((c, i) => {
          const last = i === crumbs.length - 1;
          return (
            <li key={c.path}>
              {last ? (
                <span aria-current="page">{c.name}</span>
              ) : (
                <Link href={c.path}>{c.name}</Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
