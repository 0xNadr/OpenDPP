import Link from "next/link";
import { notFound } from "next/navigation";
import { ChatDrawer } from "@/components/ChatDrawer";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { ViewSwitcher } from "@/components/ViewSwitcher";
import { ConsumerView } from "@/components/views/ConsumerView";
import { RecyclerView } from "@/components/views/RecyclerView";
import { RegulatorView } from "@/components/views/RegulatorView";
import {
  DPPNotFoundError,
  digitalLinkPath,
  fetchAnchorProofs,
  fetchCredentials,
  fetchDPP,
  fetchTranslatedDPP,
  RTL_LANGS,
  SUPPORTED_LANGS,
  type DigitalLinkParams,
  type Lang,
} from "@/lib/api";
import { parseView, VIEW_DESCRIPTIONS } from "@/lib/views";

function parseLang(raw: string | string[] | undefined): Lang {
  const v = Array.isArray(raw) ? raw[0] : raw;
  return SUPPORTED_LANGS.includes(v as Lang) ? (v as Lang) : "en";
}

export async function DPPPage({
  params,
  view: rawView,
  lang: rawLang,
}: {
  params: DigitalLinkParams;
  view: string | string[] | undefined;
  lang: string | string[] | undefined;
}) {
  const view = parseView(Array.isArray(rawView) ? rawView[0] : rawView);
  const lang = parseLang(rawLang);
  const basePath = digitalLinkPath(params);

  let dpp;
  try {
    dpp = await fetchDPP(params);
  } catch (err) {
    if (err instanceof DPPNotFoundError) notFound();
    throw err;
  }

  const recordId = dpp["opendpp:recordId"];
  const [translated, credentials, anchorProofs] = await Promise.all([
    lang !== "en" && recordId ? fetchTranslatedDPP(recordId, lang) : Promise.resolve(null),
    recordId ? fetchCredentials(recordId) : Promise.resolve([]),
    recordId ? fetchAnchorProofs(recordId) : Promise.resolve([]),
  ]);
  if (translated) {
    dpp = { ...dpp, ...translated };
  }

  const dir = RTL_LANGS.includes(lang) ? "rtl" : "ltr";

  return (
    <main
      lang={lang}
      dir={dir}
      className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-12"
    >
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between no-print">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
          aria-label="OpenDPP home"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo.svg"
            alt=""
            aria-hidden="true"
            width={20}
            height={20}
            className="h-5 w-5"
          />
          <span>OpenDPP</span>
        </Link>
        <div className="flex flex-wrap items-center gap-2">
          <ViewSwitcher basePath={basePath} current={view} />
          <LanguageSwitcher basePath={basePath} current={lang} view={view} />
        </div>
      </div>

      <p className="mb-4 text-xs text-muted-foreground no-print">
        {VIEW_DESCRIPTIONS[view]}
      </p>

      {view === "consumer" && (
        <ConsumerView dpp={dpp} credentials={credentials} />
      )}
      {view === "recycler" && <RecyclerView dpp={dpp} />}
      {view === "regulator" && (
        <RegulatorView
          dpp={dpp}
          credentials={credentials}
          anchorProofs={anchorProofs}
          recordId={recordId}
        />
      )}

      <footer className="mt-12 border-t pt-6 text-xs text-muted-foreground no-print">
        <p>
          Reference, not production. OpenDPP is an open-source educational
          implementation.
        </p>
        <p className="mt-1 font-mono">
          GS1 Digital Link: {basePath}
        </p>
      </footer>

      {dpp["opendpp:recordId"] && (
        <ChatDrawer recordId={dpp["opendpp:recordId"]} />
      )}
    </main>
  );
}
