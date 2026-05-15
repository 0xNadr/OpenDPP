import Link from "next/link";
import { SUPPORTED_LANGS, type Lang } from "@/lib/api";
import { cn } from "@/lib/utils";

const LANG_LABELS: Record<Lang, string> = {
  en: "EN",
  de: "DE",
  fr: "FR",
  ar: "AR",
};

const LANG_NAMES: Record<Lang, string> = {
  en: "English",
  de: "Deutsch",
  fr: "Français",
  ar: "العربية",
};

export function LanguageSwitcher({
  basePath,
  current,
  view,
}: {
  basePath: string;
  current: Lang;
  view: string;
}) {
  return (
    <nav aria-label="Language" className="no-print">
      <ul className="flex flex-wrap gap-1 rounded-lg bg-muted p-1 text-xs">
        {SUPPORTED_LANGS.map((lang) => {
          const active = current === lang;
          return (
            <li key={lang}>
              <Link
                href={`${basePath}?view=${view}&lang=${lang}`}
                aria-current={active ? "page" : undefined}
                aria-label={LANG_NAMES[lang]}
                title={LANG_NAMES[lang]}
                className={cn(
                  "inline-flex items-center rounded-md px-2.5 py-1 font-medium tracking-wide transition-colors",
                  active
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {LANG_LABELS[lang]}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
