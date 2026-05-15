"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { PUBLIC_API_BASE_URL } from "@/lib/api";

type Status =
  | { state: "idle" }
  | { state: "checking" }
  | { state: "valid"; issuer: string }
  | { state: "invalid"; error: string };

export function VerifyButton({ jwt }: { jwt: string }) {
  const [status, setStatus] = useState<Status>({ state: "idle" });

  async function run() {
    setStatus({ state: "checking" });
    try {
      const res = await fetch(`${PUBLIC_API_BASE_URL}/api/vc/verify`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ jwt }),
      });
      const body = (await res.json()) as {
        valid: boolean;
        issuer: string | null;
        error: string | null;
      };
      if (body.valid && body.issuer) {
        setStatus({ state: "valid", issuer: body.issuer });
      } else {
        setStatus({ state: "invalid", error: body.error ?? "unknown error" });
      }
    } catch (err) {
      setStatus({
        state: "invalid",
        error: `network error: ${(err as Error).message}`,
      });
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => void run()}
        disabled={status.state === "checking"}
      >
        {status.state === "checking" ? "Verifying…" : "Verify signature"}
      </Button>
      {status.state === "valid" && (
        <span className="text-sm text-emerald-700 dark:text-emerald-400">
          ✓ Valid · signed by{" "}
          <code className="text-xs">{status.issuer}</code>
        </span>
      )}
      {status.state === "invalid" && (
        <span className="text-sm text-red-700 dark:text-red-400">
          ✗ Invalid · {status.error}
        </span>
      )}
    </div>
  );
}
