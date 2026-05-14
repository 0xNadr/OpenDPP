"use client";

import { QRCodeSVG } from "qrcode.react";

export function DPPQrCode({
  url,
  size = 160,
  alt,
}: {
  url: string;
  size?: number;
  alt: string;
}) {
  return (
    <QRCodeSVG
      value={url}
      size={size}
      level="M"
      marginSize={2}
      role="img"
      aria-label={alt}
    />
  );
}
