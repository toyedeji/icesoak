"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import type { Studio } from "@/lib/types";
import StudioCard from "./StudioCard";
import { mods } from "@/lib/studios";

// Map is browser-only; load it lazily so static export builds without it.
const StudioMap = dynamic(() => import("./StudioMap"), {
  ssr: false,
  loading: () => <div className="map map--loading" aria-hidden="true" />,
});

interface Props {
  studios: Studio[];
  center: { lat: number; lng: number };
}

const FILTERS: { key: string; label: string; test: (s: Studio) => boolean }[] = [
  { key: "all", label: "All", test: () => true },
  { key: "cold_plunge", label: "Cold plunge", test: (s) => mods(s).includes("cold_plunge") },
  { key: "sauna_infrared", label: "Infrared sauna", test: (s) => mods(s).includes("sauna_infrared") },
  {
    key: "sauna_traditional",
    label: "Traditional sauna",
    test: (s) => mods(s).includes("sauna_traditional"),
  },
  { key: "contrast", label: "Contrast", test: (s) => mods(s).includes("cold_plunge") && mods(s).some((m) => m.startsWith("sauna")) },
];

// Filters run client-side over an already server-rendered list, so the full set
// of studios is present in the static HTML for crawlers; filtering only toggles
// what a human sees.
export default function StudioExplorer({ studios, center }: Props) {
  const [active, setActive] = useState("all");
  const [q, setQ] = useState("");

  // Only show filter chips that actually match at least one studio here.
  const available = useMemo(
    () => FILTERS.filter((f) => f.key === "all" || studios.some(f.test)),
    [studios],
  );

  const visible = useMemo(() => {
    const f = FILTERS.find((x) => x.key === active) ?? FILTERS[0];
    const needle = q.trim().toLowerCase();
    return studios.filter(
      (s) =>
        f.test(s) &&
        (needle === "" ||
          s.name.toLowerCase().includes(needle) ||
          (s.city ?? "").toLowerCase().includes(needle) ||
          (s.neighborhood ?? "").toLowerCase().includes(needle)),
    );
  }, [studios, active, q]);

  return (
    <div className="explorer">
      <StudioMap studios={visible} center={center} />

      <div className="explorer__controls">
        <div className="chips" role="group" aria-label="Filter by modality">
          {available.map((f) => (
            <button
              key={f.key}
              type="button"
              className={`chip${active === f.key ? " chip--active" : ""}`}
              aria-pressed={active === f.key}
              onClick={() => setActive(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <input
          type="search"
          className="explorer__search"
          placeholder="Search by name or area"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search studios"
        />
      </div>

      <p className="explorer__count">
        {visible.length} {visible.length === 1 ? "studio" : "studios"}
      </p>

      <div className="grid">
        {visible.map((s) => (
          <StudioCard key={s.id} studio={s} />
        ))}
      </div>
    </div>
  );
}
