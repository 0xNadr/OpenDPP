import type { TextileDigitalProductPassport } from "@/lib/generated/textile-dpp";

const API_BASE_URL =
  process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type DPPJsonLd = TextileDigitalProductPassport & {
  "@context"?: Record<string, string>;
  "@type"?: string | string[];
  "@id"?: string;
};

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
