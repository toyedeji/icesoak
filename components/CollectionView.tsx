import Breadcrumbs from "./Breadcrumbs";
import AnswerCapsule from "./AnswerCapsule";
import StudioExplorer from "./StudioExplorer";
import JsonLd from "./JsonLd";
import type { Studio } from "@/lib/types";
import type { Crumb } from "@/lib/jsonld";

interface Props {
  crumbs: Crumb[];
  h1: string;
  capsule: string;
  studios: Studio[];
  center: { lat: number; lng: number };
  jsonLd: unknown[];
  indexable: boolean;
  intro?: React.ReactNode;
  children?: React.ReactNode;
}

// Shared layout for every directory/list page: one H1, breadcrumbs, answer
// capsule, map+filters, structured data, and a noindex notice when thin.
export default function CollectionView({
  crumbs,
  h1,
  capsule,
  studios,
  center,
  jsonLd,
  indexable,
  intro,
  children,
}: Props) {
  return (
    <div className="wrap">
      <JsonLd data={jsonLd} />
      <Breadcrumbs crumbs={crumbs} />
      <h1>{h1}</h1>
      <AnswerCapsule text={capsule} />
      {!indexable && (
        <p className="notice">
          This page lists fewer than three verified studios, so it is marked
          noindex until coverage grows. The listings below are still accurate.
        </p>
      )}
      {intro && <div className="section">{intro}</div>}
      {studios.length > 0 ? (
        <StudioExplorer studios={studios} center={center} />
      ) : (
        <p className="muted">No verified studios are listed here yet.</p>
      )}
      {children}
    </div>
  );
}
