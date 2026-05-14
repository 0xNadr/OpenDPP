export const VIEW_TYPES = ["consumer", "recycler", "regulator"] as const;
export type ViewType = (typeof VIEW_TYPES)[number];

export function parseView(input: unknown): ViewType {
  if (typeof input === "string" && (VIEW_TYPES as readonly string[]).includes(input)) {
    return input as ViewType;
  }
  return "consumer";
}

export const VIEW_LABELS: Record<ViewType, string> = {
  consumer: "Consumer",
  recycler: "Recycler",
  regulator: "Regulator",
};

export const VIEW_DESCRIPTIONS: Record<ViewType, string> = {
  consumer: "What a shopper sees when they scan the product.",
  recycler: "Material composition, substances of concern, end-of-life pathways.",
  regulator: "Full record with certifications, supply chain, and raw JSON-LD.",
};
