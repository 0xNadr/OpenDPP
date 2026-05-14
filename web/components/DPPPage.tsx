import Link from "next/link";
import { notFound } from "next/navigation";
import { ConsumerView } from "@/components/views/ConsumerView";
import { RecyclerView } from "@/components/views/RecyclerView";
import { RegulatorView } from "@/components/views/RegulatorView";
import { ViewSwitcher } from "@/components/ViewSwitcher";
import {
  DPPNotFoundError,
  digitalLinkPath,
  fetchDPP,
  type DigitalLinkParams,
} from "@/lib/api";
import { parseView, VIEW_DESCRIPTIONS } from "@/lib/views";

export async function DPPPage({
  params,
  view: rawView,
}: {
  params: DigitalLinkParams;
  view: string | string[] | undefined;
}) {
  const view = parseView(Array.isArray(rawView) ? rawView[0] : rawView);
  const basePath = digitalLinkPath(params);

  let dpp;
  try {
    dpp = await fetchDPP(params);
  } catch (err) {
    if (err instanceof DPPNotFoundError) notFound();
    throw err;
  }

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between no-print">
        <Link
          href="/"
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          ← OpenDPP
        </Link>
        <ViewSwitcher basePath={basePath} current={view} />
      </div>

      <p className="mb-4 text-xs text-muted-foreground no-print">
        {VIEW_DESCRIPTIONS[view]}
      </p>

      {view === "consumer" && <ConsumerView dpp={dpp} />}
      {view === "recycler" && <RecyclerView dpp={dpp} />}
      {view === "regulator" && <RegulatorView dpp={dpp} />}

      <footer className="mt-12 border-t pt-6 text-xs text-muted-foreground no-print">
        <p>
          Reference, not production. OpenDPP is an open-source educational
          implementation.
        </p>
        <p className="mt-1 font-mono">
          GS1 Digital Link: {basePath}
        </p>
      </footer>
    </main>
  );
}
