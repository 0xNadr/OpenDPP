import { DPPPage } from "@/components/DPPPage";

export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ gtin: string; lot: string }>;
  searchParams: Promise<{ view?: string; lang?: string }>;
}) {
  const { gtin, lot } = await params;
  const { view, lang } = await searchParams;
  return <DPPPage params={{ gtin, lot }} view={view} lang={lang} />;
}
