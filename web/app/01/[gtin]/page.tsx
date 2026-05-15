import { DPPPage } from "@/components/DPPPage";

export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ gtin: string }>;
  searchParams: Promise<{ view?: string; lang?: string }>;
}) {
  const { gtin } = await params;
  const { view, lang } = await searchParams;
  return <DPPPage params={{ gtin }} view={view} lang={lang} />;
}
