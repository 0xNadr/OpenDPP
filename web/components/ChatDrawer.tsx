"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { PUBLIC_API_BASE_URL } from "@/lib/api";
import { cn } from "@/lib/utils";

type Turn = { role: "user" | "assistant"; content: string };

export function ChatDrawer({ recordId }: { recordId: string }) {
  const [open, setOpen] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  async function send() {
    const question = input.trim();
    if (!question || streaming) return;
    setInput("");
    const next: Turn[] = [...turns, { role: "user", content: question }];
    setTurns(next);
    setStreaming(true);
    setTurns((t) => [...t, { role: "assistant", content: "" }]);

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      const res = await fetch(
        `${PUBLIC_API_BASE_URL}/api/chat/${encodeURIComponent(recordId)}`,
        {
          method: "POST",
          headers: { "content-type": "application/json", accept: "text/event-stream" },
          body: JSON.stringify({ messages: next }),
          signal: ctrl.signal,
        },
      );
      if (!res.ok || !res.body) {
        throw new Error(`chat HTTP ${res.status}`);
      }
      await consumeSSE(res.body, (event, data) => {
        if (event === "delta") {
          setTurns((t) => {
            const copy = [...t];
            copy[copy.length - 1] = {
              role: "assistant",
              content: copy[copy.length - 1].content + data,
            };
            return copy;
          });
        } else if (event === "error") {
          setTurns((t) => {
            const copy = [...t];
            copy[copy.length - 1] = {
              role: "assistant",
              content: `(error: ${data})`,
            };
            return copy;
          });
        }
      });
    } catch (err) {
      if ((err as { name?: string }).name !== "AbortError") {
        setTurns((t) => {
          const copy = [...t];
          copy[copy.length - 1] = {
            role: "assistant",
            content: `(network error: ${(err as Error).message})`,
          };
          return copy;
        });
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  }

  return (
    <>
      <div className="fixed bottom-4 right-4 z-50 no-print">
        <Button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls="opendpp-chat"
          className="shadow-lg"
        >
          {open ? "Close" : "Ask about this product"}
        </Button>
      </div>

      {open && (
        <aside
          id="opendpp-chat"
          className={cn(
            "fixed bottom-20 right-4 z-40 flex w-[min(90vw,28rem)] flex-col rounded-xl border bg-background p-4 shadow-xl no-print",
            "max-h-[70vh]",
          )}
          aria-label="Product Q&A"
        >
          <header className="mb-2 flex items-center justify-between border-b pb-2">
            <strong className="text-sm">Ask about this product</strong>
            <span className="text-xs text-muted-foreground">
              Answers are grounded in this DPP only.
            </span>
          </header>

          <div className="mb-3 flex-1 overflow-y-auto rounded-md bg-muted/40 p-3 text-sm">
            {turns.length === 0 && (
              <p className="text-muted-foreground">
                Try: <em>“What is this product made of?”</em>
              </p>
            )}
            <ul className="space-y-3">
              {turns.map((t, i) => (
                <li
                  key={i}
                  className={cn(
                    t.role === "user" ? "text-foreground" : "text-muted-foreground",
                  )}
                >
                  <span className="mr-2 inline-block rounded-full bg-background px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide">
                    {t.role}
                  </span>
                  <span className="whitespace-pre-wrap">{t.content || (streaming && i === turns.length - 1 ? "…" : "")}</span>
                </li>
              ))}
            </ul>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
            className="flex gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question…"
              aria-label="Question"
              className="flex-1 rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              disabled={streaming}
            />
            <Button type="submit" disabled={streaming || !input.trim()}>
              {streaming ? "…" : "Send"}
            </Button>
          </form>
        </aside>
      )}
    </>
  );
}

async function consumeSSE(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: string, data: string) => void,
) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let event = "message";
  let data = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let idx;
    while ((idx = buffer.indexOf("\n")) !== -1) {
      const line = buffer.slice(0, idx).replace(/\r$/, "");
      buffer = buffer.slice(idx + 1);

      if (line === "") {
        if (data) onEvent(event, data);
        event = "message";
        data = "";
        continue;
      }
      if (line.startsWith("event:")) {
        event = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        data += line.slice(5).replace(/^ /, "");
      }
    }
  }
}
