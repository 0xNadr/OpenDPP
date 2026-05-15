import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// `metadataBase` is read at SSR time on the server side, so we use a plain
// env var (not NEXT_PUBLIC_*). Falls through to NEXT_PUBLIC_SITE_URL if a
// dedicated SITE_URL isn't set, since they typically match.
const SITE_URL =
  process.env.SITE_URL ??
  process.env.NEXT_PUBLIC_SITE_URL ??
  "http://localhost:3030";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "OpenDPP — Digital Product Passport",
    template: "%s · OpenDPP",
  },
  description:
    "OpenDPP — open-source reference implementation of an EU Digital Product Passport. Standards-correct GS1, W3C, and ESPR-informed, with verifiable credentials and on-chain tamper-evidence.",
  applicationName: "OpenDPP",
  openGraph: {
    type: "website",
    siteName: "OpenDPP",
    title: "OpenDPP — Digital Product Passport",
    description:
      "Open-source reference implementation of an EU Digital Product Passport.",
    url: SITE_URL,
    images: [
      {
        url: `${SITE_URL}/opengraph-image.png`,
        width: 1200,
        height: 630,
        alt: "OpenDPP — open-source reference Digital Product Passport",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "OpenDPP — Digital Product Passport",
    description:
      "Open-source reference implementation of an EU Digital Product Passport.",
    images: [`${SITE_URL}/opengraph-image.png`],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      dir="ltr"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        {children}
      </body>
    </html>
  );
}
