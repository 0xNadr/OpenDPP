import { DPPPage } from "@/components/DPPPage";

export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ gtin: string }>;
  searchParams: Promise<{ view?: string }>;
}) {
  const { gtin } = await params;
  const { view } = await searchParams;
  return <DPPPage params={{ gtin }} view={view} />;
}
