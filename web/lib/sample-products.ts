import type { DigitalLinkParams } from "@/lib/api";

export type SampleProduct = {
  name: string;
  brand: string;
  blurb: string;
  link: DigitalLinkParams;
};

export const SAMPLE_PRODUCTS: SampleProduct[] = [
  {
    name: "Atelier Organic Cotton Tee",
    brand: "Atelier",
    blurb: "95% organic cotton tee, made in Portugal. GOTS-certified.",
    link: { gtin: "07350053850010", lot: "ATL-2026-T01" },
  },
  {
    name: "Northwave Recycled Denim Jeans",
    brand: "Northwave",
    blurb: "70% recycled cotton jeans, GRS + OEKO-TEX certified.",
    link: { gtin: "07350053850027", lot: "NW-2026-D02" },
  },
  {
    name: "Soraya Wool–Linen Jacket",
    brand: "Soraya",
    blurb: "60% Responsible Wool / 38% European Linen jacket, individually serialized.",
    link: {
      gtin: "07350053850034",
      lot: "SOR-2026-J03",
      serial: "SOR-J03-000142",
    },
  },
];
