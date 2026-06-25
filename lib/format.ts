// Safe rendering helpers. The data has many nullable fields; we must NEVER render
// the literal string "null" and should omit missing values gracefully.

export function present<T>(v: T | null | undefined): v is T {
  if (v === null || v === undefined) return false;
  if (typeof v === "string") {
    const t = v.trim().toLowerCase();
    return t !== "" && t !== "null" && t !== "undefined";
  }
  if (Array.isArray(v)) return v.length > 0;
  return true;
}

// Use for optional display: returns the value only if genuinely present, else undefined.
export function val<T>(v: T | null | undefined): T | undefined {
  return present(v) ? (v as T) : undefined;
}

export function usd(n: number | null | undefined): string | undefined {
  return present(n) ? `$${Number(n).toFixed(0)}` : undefined;
}

export function tempRange(
  min: number | null | undefined,
  max: number | null | undefined,
): string | undefined {
  const lo = val(min);
  const hi = val(max);
  if (lo !== undefined && hi !== undefined) return lo === hi ? `${lo}°F` : `${lo}–${hi}°F`;
  if (lo !== undefined) return `from ${lo}°F`;
  if (hi !== undefined) return `up to ${hi}°F`;
  return undefined;
}

export function slugify(s: string): string {
  return s
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

// Human label for a modality code.
const MODALITY_LABELS: Record<string, string> = {
  cold_plunge: "Cold plunge",
  sauna_infrared: "Infrared sauna",
  sauna_traditional: "Traditional sauna",
  sauna: "Sauna",
  contrast: "Contrast therapy",
  cryo: "Cryotherapy",
  red_light: "Red-light therapy",
  compression: "Compression",
  iv: "IV therapy",
};

export function modalityLabel(code: string): string {
  return MODALITY_LABELS[code] ?? code.replace(/_/g, " ");
}

export function listModalities(codes: string[] | null | undefined): string {
  if (!present(codes)) return "";
  return (codes as string[]).map(modalityLabel).join(", ");
}

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

// Format an ISO date (YYYY-MM-DD) as "June 25, 2026" without relying on Date parsing/timezones.
export function formatDate(iso: string | null | undefined): string | undefined {
  if (!present(iso)) return undefined;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso as string);
  if (!m) return val(iso);
  const year = m[1];
  const month = MONTHS[parseInt(m[2], 10) - 1];
  const day = parseInt(m[3], 10);
  if (!month) return val(iso);
  return `${month} ${day}, ${year}`;
}
