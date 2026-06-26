import { verticalStaticParams, verticalMetadata, VerticalCityPage, type CityParams } from "@/lib/verticalPage";

const V = "infrared-sauna" as const;

export function generateStaticParams() {
  return verticalStaticParams(V);
}

export async function generateMetadata({ params }: { params: Promise<CityParams> }) {
  return verticalMetadata(V, await params);
}

export default async function Page({ params }: { params: Promise<CityParams> }) {
  return VerticalCityPage(V, await params);
}
