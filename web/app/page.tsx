import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DPPQrCode } from "@/components/DPPQrCode";
import { digitalLinkPath } from "@/lib/api";
import { SAMPLE_PRODUCTS } from "@/lib/sample-products";

const SITE_BASE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-12">
      <header className="mb-12">
        <div className="flex items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo.svg"
            alt=""
            aria-hidden="true"
            width={48}
            height={48}
            className="h-12 w-12"
          />
          <h1 className="text-4xl font-semibold tracking-tight">OpenDPP</h1>
        </div>
        <p className="mt-3 max-w-2xl text-muted-foreground">
          Open-source reference Digital Product Passport. Three sample textile
          products below, each with a scannable GS1 Digital Link QR.
        </p>
        <div className="mt-4 flex flex-wrap gap-2 text-xs">
          <Badge variant="outline">GS1 Digital Link 1.4</Badge>
          <Badge variant="outline">GS1 EPCIS 2.0</Badge>
          <Badge variant="outline">W3C JSON-LD</Badge>
          <Badge variant="outline">ESPR-aligned</Badge>
        </div>
      </header>

      <section aria-labelledby="samples-heading">
        <h2 id="samples-heading" className="text-lg font-semibold mb-4">
          Sample products
        </h2>
        <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {SAMPLE_PRODUCTS.map((p) => {
            const path = digitalLinkPath(p.link);
            const url = `${SITE_BASE_URL}${path}`;
            return (
              <li key={p.link.gtin + (p.link.serial ?? "")}>
                <Card className="h-full">
                  <CardHeader>
                    <p className="text-xs font-medium text-muted-foreground">{p.brand}</p>
                    <CardTitle className="text-base">{p.name}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-muted-foreground">{p.blurb}</p>
                    <div className="flex items-center justify-center rounded-md border bg-white p-3">
                      <DPPQrCode url={url} alt={`QR code for ${p.name}`} size={160} />
                    </div>
                    <p className="break-all font-mono text-[10px] text-muted-foreground">
                      {path}
                    </p>
                    <Link
                      href={path}
                      className="inline-block text-sm font-medium underline-offset-4 hover:underline"
                    >
                      Open passport →
                    </Link>
                  </CardContent>
                </Card>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="mt-16 text-sm text-muted-foreground" aria-labelledby="about-heading">
        <h2 id="about-heading" className="mb-2 text-lg font-semibold text-foreground">
          What is this?
        </h2>
        <p>
          OpenDPP is an open-source reference implementation of a Digital
          Product Passport for the European market. The passports above are
          real records served from the OpenDPP API, identified using GS1
          Digital Link URLs.
        </p>
        <p className="mt-2">
          Each product has three audience-specific views: a{" "}
          <span className="font-medium text-foreground">consumer</span> view (what a shopper
          sees), a <span className="font-medium text-foreground">recycler</span> view (material
          composition, end-of-life pathways), and a{" "}
          <span className="font-medium text-foreground">regulator</span> view (full compliance
          and supply chain).
        </p>
      </section>

      <footer className="mt-16 border-t pt-6 text-xs text-muted-foreground">
        Reference, not production. MIT-licensed at{" "}
        <a
          href="https://github.com/0xNadr/OpenDPP"
          className="underline-offset-4 hover:underline"
        >
          github.com/0xNadr/OpenDPP
        </a>
        .
      </footer>
    </main>
  );
}
