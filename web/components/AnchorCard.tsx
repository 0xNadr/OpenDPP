"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AnchorProof } from "@/lib/api";
import { PUBLIC_API_BASE_URL } from "@/lib/api";

type VerifyState =
  | { state: "idle" }
  | { state: "checking" }
  | {
      state: "ok";
      timestamp: number;
      matches_stored: boolean;
      current_hash: string;
    }
  | { state: "no_anchor"; current_hash: string }
  | { state: "error"; message: string };

export function AnchorCard({
  recordId,
  proofs,
}: {
  recordId: string;
  proofs: AnchorProof[];
}) {
  const [verify, setVerify] = useState<VerifyState>({ state: "idle" });

  async function runVerify() {
    setVerify({ state: "checking" });
    try {
      const res = await fetch(
        `${PUBLIC_API_BASE_URL}/api/anchor/${encodeURIComponent(recordId)}/verify`,
        { method: "GET", cache: "no-store" },
      );
      if (!res.ok) {
        setVerify({ state: "error", message: `HTTP ${res.status}` });
        return;
      }
      const body = (await res.json()) as {
        chain: string;
        current_snapshot_hash: string;
        anchored: boolean;
        on_chain_timestamp: number;
        matches_stored_proof: boolean;
      };
      if (!body.anchored) {
        setVerify({ state: "no_anchor", current_hash: body.current_snapshot_hash });
        return;
      }
      setVerify({
        state: "ok",
        timestamp: body.on_chain_timestamp,
        matches_stored: body.matches_stored_proof,
        current_hash: body.current_snapshot_hash,
      });
    } catch (err) {
      setVerify({
        state: "error",
        message: `network error: ${(err as Error).message}`,
      });
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>On-chain anchor</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {proofs.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            This DPP snapshot has not been anchored yet.
          </p>
        ) : (
          proofs.map((p) => (
            <div
              key={p.id}
              className="space-y-2 rounded-md border bg-muted/40 p-3"
            >
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="default" className="bg-emerald-600">
                  Anchored
                </Badge>
                <span className="text-sm">
                  on <strong className="font-mono">{p.chain}</strong> at block{" "}
                  <span className="font-mono">{p.block_number}</span>
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Anchored at <span className="font-mono">{p.anchored_at}</span>
              </p>
              <p className="font-mono text-xs break-all">
                <span className="text-muted-foreground">snapshot: </span>
                {p.snapshot_hash}
              </p>
              <p className="font-mono text-xs break-all">
                <span className="text-muted-foreground">tx: </span>
                {p.explorer_tx_url ? (
                  <a
                    href={p.explorer_tx_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-700 hover:underline dark:text-emerald-400"
                  >
                    {p.tx_hash} ↗
                  </a>
                ) : (
                  p.tx_hash
                )}
              </p>
            </div>
          ))
        )}

        <div className="space-y-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => void runVerify()}
            disabled={verify.state === "checking"}
          >
            {verify.state === "checking"
              ? "Verifying on-chain…"
              : "Re-verify anchor on-chain"}
          </Button>
          <p className="text-xs text-muted-foreground">
            Re-hashes the current DPP and queries the contract directly,
            independent of this server.
          </p>

          {verify.state === "ok" && (
            <div className="rounded-md border border-emerald-500/40 bg-emerald-50 p-2 text-sm text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-100">
              ✓ Current snapshot is anchored on{" "}
              <strong>{proofs[0]?.chain ?? "chain"}</strong>{" "}
              {verify.matches_stored ? "and matches the stored proof." : "(no matching stored proof)."}
              <br />
              <span className="font-mono text-xs">
                on-chain timestamp: {verify.timestamp}
              </span>
            </div>
          )}
          {verify.state === "no_anchor" && (
            <div className="rounded-md border border-amber-500/40 bg-amber-50 p-2 text-sm text-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
              ✗ Current snapshot is <strong>not</strong> anchored. Either the
              DPP has been edited since anchoring, or no anchor has been
              issued.
              <br />
              <span className="font-mono text-xs break-all">
                current hash: {verify.current_hash}
              </span>
            </div>
          )}
          {verify.state === "error" && (
            <div className="rounded-md border border-red-500/40 bg-red-50 p-2 text-sm text-red-900 dark:bg-red-950/40 dark:text-red-100">
              ✗ Verification error · {verify.message}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
