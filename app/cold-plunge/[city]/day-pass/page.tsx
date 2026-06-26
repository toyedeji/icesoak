import { facetStaticParams, facetMetadata, FacetPage } from "@/lib/facetPage";

const F = "day-pass" as const;
type P = { params: Promise<{ city: string }> };

export function generateStaticParams() {
  return facetStaticParams(F);
}

export async function generateMetadata({ params }: P) {
  return facetMetadata(F, await params);
}

export default async function Page({ params }: P) {
  return FacetPage(F, await params);
}
