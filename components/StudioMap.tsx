"use client";

import { useEffect, useRef } from "react";
import "leaflet/dist/leaflet.css";
import type { Studio } from "@/lib/types";

interface Props {
  studios: Studio[];
  center: { lat: number; lng: number };
  zoom?: number;
}

// Leaflet is loaded only in the browser (inside useEffect), so static export
// never tries to render it on the server. Uses free OpenStreetMap tiles — no API key.
// circleMarker avoids the bundler-broken default marker image assets.
export default function StudioMap({ studios, center, zoom = 11 }: Props) {
  const elRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<unknown>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const L = (await import("leaflet")).default;
      if (cancelled || !elRef.current || mapRef.current) return;

      const map = L.map(elRef.current, { scrollWheelZoom: false }).setView(
        [center.lat, center.lng],
        zoom,
      );
      mapRef.current = map;

      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(map);

      const located = studios.filter(
        (s) => typeof s.lat === "number" && typeof s.lng === "number",
      );
      const bounds: [number, number][] = [];
      for (const s of located) {
        const lat = s.lat as number;
        const lng = s.lng as number;
        L.circleMarker([lat, lng], {
          radius: 8,
          color: "#0b6e99",
          fillColor: "#16a3d8",
          fillOpacity: 0.85,
          weight: 2,
        })
          .addTo(map)
          .bindPopup(`<strong>${s.name}</strong>`);
        bounds.push([lat, lng]);
      }
      if (bounds.length > 1) map.fitBounds(bounds, { padding: [30, 30] });
    })();

    return () => {
      cancelled = true;
      const m = mapRef.current as { remove?: () => void } | null;
      if (m && typeof m.remove === "function") m.remove();
      mapRef.current = null;
    };
  }, [studios, center.lat, center.lng, zoom]);

  const locatedCount = studios.filter(
    (s) => typeof s.lat === "number" && typeof s.lng === "number",
  ).length;

  return (
    <div className="map">
      <div ref={elRef} className="map__canvas" role="application" aria-label="Studio map" />
      {locatedCount === 0 && (
        <p className="map__note">
          Precise pins for these studios are being verified. Locations are listed below.
        </p>
      )}
    </div>
  );
}
