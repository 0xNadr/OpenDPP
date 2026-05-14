import { DPPPage } from "@/components/DPPPage";

export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ gtin: string; lot: string }>;
  searchParams: Promise<{ view?: string }>;
}) {
  const { gtin, lot } = await params;
  const { view } = await searchParams;
  return <DPPPage params={{ gtin, lot }} view={view} />;
}
