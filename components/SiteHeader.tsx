import Link from "next/link";
import { SITE } from "@/lib/site";
import { METROS } from "@/lib/data";

export default function SiteHeader() {
  return (
    <header className="site-header">
      <div className="wrap site-header__inner">
        <Link href="/" className="brand" aria-label={`${SITE.name} home`}>
          <span className="brand__mark" aria-hidden="true">❄</span>
          <span className="brand__name">{SITE.name}</span>
        </Link>
        <nav aria-label="Primary" className="site-nav">
          <Link href="/cold-plunge/denver/">Cold plunge</Link>
          <Link href="/sauna/denver/">Sauna</Link>
          <Link href="/guides/">Guides</Link>
          <span className="site-nav__metros">
            {METROS.map((m) => (
              <Link key={m.slug} href={`/cold-plunge/${m.slug}/`}>
                {m.name}
              </Link>
            ))}
          </span>
        </nav>
      </div>
    </header>
  );
}
