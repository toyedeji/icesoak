import Link from "next/link";
import { SITE } from "@/lib/site";
import { METROS } from "@/lib/data";

export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="wrap site-footer__grid">
        <div>
          <p className="brand brand--footer">
            <span aria-hidden="true">❄</span> {SITE.name}
          </p>
          <p className="muted">{SITE.tagline}</p>
        </div>
        <nav aria-label="Metros">
          <h2 className="footer__h">Metros</h2>
          <ul>
            {METROS.map((m) => (
              <li key={m.slug}>
                <Link href={`/cold-plunge/${m.slug}/`}>
                  {m.name}, {m.state}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <nav aria-label="Resources">
          <h2 className="footer__h">Resources</h2>
          <ul>
            <li><Link href="/guides/">Guides</Link></li>
            <li><Link href="/cold-plunge-vs-ice-bath/">Cold plunge vs ice bath</Link></li>
            <li><Link href="/infrared-vs-traditional-sauna/">Infrared vs traditional sauna</Link></li>
          </ul>
        </nav>
      </div>
      <div className="wrap site-footer__legal">
        <p className="muted">
          © 2026 {SITE.name}. Listings are informational; verify details and medical
          guidance independently.
        </p>
      </div>
    </footer>
  );
}
