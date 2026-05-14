import Link from "next/link";
import { VIEW_LABELS, VIEW_TYPES, type ViewType } from "@/lib/views";
import { cn } from "@/lib/utils";

export function ViewSwitcher({
  basePath,
  current,
}: {
  basePath: string;
  current: ViewType;
}) {
  return (
    <nav aria-label="Audience" className="no-print">
      <ul className="flex flex-wrap gap-1 rounded-lg bg-muted p-1 text-sm">
        {VIEW_TYPES.map((view) => {
          const active = current === view;
          return (
            <li key={view}>
              <Link
                href={`${basePath}?view=${view}`}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "inline-flex items-center rounded-md px-3 py-1.5 font-medium transition-colors",
                  active
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {VIEW_LABELS[view]}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
