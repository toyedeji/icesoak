import Script from "next/script";
import { ANALYTICS_ENABLED, GA4_MEASUREMENT_ID } from "@/lib/analytics";

/**
 * GA4 loader. Renders nothing at all when NEXT_PUBLIC_GA4_MEASUREMENT_ID is
 * unset — no script tag pointing at an empty ID, no console error, no
 * half-initialised gtag stub.
 *
 * Note on this site specifically: next.config.mjs sets output: 'export', so
 * these tags are baked into every exported .html file rather than injected by a
 * running server. That is why scripts/assert-build.mjs can read them straight
 * out of out/ — and why a build with the env var missing ships 372 pages with
 * no tag at all and nothing to notice at runtime. The gate exists for that.
 */
export default function Analytics() {
  if (!ANALYTICS_ENABLED) return null;

  return (
    <>
      <Script
        src={`https://www.googletagmanager.com/gtag/js?id=${GA4_MEASUREMENT_ID}`}
        strategy="afterInteractive"
      />
      <Script id="ga4-init" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          window.gtag = gtag;
          gtag('js', new Date());
          gtag('config', '${GA4_MEASUREMENT_ID}');
        `}
      </Script>
    </>
  );
}
