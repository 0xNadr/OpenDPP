import type { TextileDigitalProductPassport } from "@/lib/generated/textile-dpp";

const API_BASE_URL =
  process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type DPPJsonLd = TextileDigitalProductPassport & {
  "@context"?: Record<string, string>;
  "@type"?: string | string[];
  "@id"?: string;
  "opendpp:recordId"?: string;
};

export const SUPPORTED_LANGS = ["en", "de", "fr", "ar"] as const;
export type Lang = (typeof SUPPORTED_LANGS)[number];
export const RTL_LANGS: Lang[] = ["ar"];

export type DigitalLinkParams = {
  gtin: string;
  lot?: string;
  serial?: string;
};

export function digitalLinkPath({ gtin, lot, serial }: DigitalLinkParams): string {
  let path = `/01/${encodeURIComponent(gtin)}`;
  if (lot !== undefined) path += `/10/${encodeURIComponent(lot)}`;
  if (serial !== undefined) path += `/21/${encodeURIComponent(serial)}`;
  return path;
}

export class DPPNotFoundError extends Error {}

export async function fetchDPP(params: DigitalLinkParams): Promise<DPPJsonLd> {
  const url = `${API_BASE_URL}${digitalLinkPath(params)}`;
  const res = await fetch(url, {
    headers: { Accept: "application/ld+json" },
    cache: "no-store",
  });
  if (res.status === 404) {
    throw new DPPNotFoundError(`No DPP found for ${digitalLinkPath(params)}`);
  }
  if (!res.ok) {
    throw new Error(`API error ${res.status} fetching ${url}`);
  }
  return (await res.json()) as DPPJsonLd;
}

export function qrUrl(
  params: DigitalLinkParams,
  opts: { format?: "svg" | "png"; size?: number } = {},
): string {
  const q = new URLSearchParams();
  if (opts.format) q.set("format", opts.format);
  if (opts.size) q.set("size", String(opts.size));
  const qs = q.toString();
  return `${API_BASE_URL}/api/qr${digitalLinkPath(params)}${qs ? `?${qs}` : ""}`;
}

/** Server-side helper: fetch a DPP translated into `lang`. Returns the
 *  translated `data` payload (same shape as the JSON-LD body, without
 *  the @context wrapper). Falls back to the original if the API errors.
 */
export async function fetchTranslatedDPP(
  recordId: string,
  lang: Lang,
): Promise<TextileDigitalProductPassport | null> {
  if (lang === "en") return null;
  const res = await fetch(
    `${API_BASE_URL}/api/dpp/${encodeURIComponent(recordId)}/translate?lang=${lang}`,
    { cache: "no-store" },
  );
  if (!res.ok) return null;
  const body = (await res.json()) as {
    data: TextileDigitalProductPassport;
    lang: Lang;
    cached: boolean;
  };
  return body.data;
}

/** Browser-visible API base URL. The web container talks to `api:8000`
 *  server-side (RSC), but the browser must hit the host-mapped port. */
export const PUBLIC_API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8080";

export type VerifiableCredential = {
  id: string;
  attestation_type: string;
  subject_id: string;
  jwt: string;
  body: {
    issuer: string;
    validFrom?: string;
    type: string[];
    credentialSubject: Record<string, unknown> & {
      certificationScheme?: string;
      certificationId?: string;
    };
    [k: string]: unknown;
  };
  supplier: { name: string; did: string };
};

export async function fetchCredentials(recordId: string): Promise<VerifiableCredential[]> {
  const res = await fetch(`${API_BASE_URL}/api/vc/dpp/${encodeURIComponent(recordId)}`, {
    cache: "no-store",
  });
  if (!res.ok) return [];
  return (await res.json()) as VerifiableCredential[];
}

export type AnchorProof = {
  id: string;
  chain: string;
  snapshot_hash: string;
  tx_hash: string;
  block_number: number;
  explorer_tx_url: string | null;
  anchored_at: string;
};

export async function fetchAnchorProofs(recordId: string): Promise<AnchorProof[]> {
  const res = await fetch(
    `${API_BASE_URL}/api/anchor/${encodeURIComponent(recordId)}/proof`,
    { cache: "no-store" },
  );
  if (!res.ok) return [];
  return (await res.json()) as AnchorProof[];
}
