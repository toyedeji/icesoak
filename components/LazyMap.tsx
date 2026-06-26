"use client";

import dynamic from "next/dynamic";
import type { Studio } from "@/lib/types";

const StudioMap = dynamic(() => import("./StudioMap"), {
  ssr: false,
  loading: () => <div className="map map--loading" aria-hidden="true" />,
});

export default function LazyMap(props: {
  studios: Studio[];
  center: { lat: number; lng: number };
  zoom?: number;
}) {
  return <StudioMap {...props} />;
}
