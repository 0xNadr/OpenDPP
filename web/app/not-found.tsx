import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-start px-6 py-16">
      <h1 className="text-3xl font-semibold tracking-tight">No passport found</h1>
      <p className="mt-3 text-muted-foreground">
        We couldn't find a Digital Product Passport at that URL. Double-check
        the GTIN, lot, and serial — or head back to the sample products.
      </p>
      <Link
        href="/"
        className="mt-6 inline-block text-sm font-medium underline-offset-4 hover:underline"
      >
        ← OpenDPP samples
      </Link>
    </main>
  );
}
