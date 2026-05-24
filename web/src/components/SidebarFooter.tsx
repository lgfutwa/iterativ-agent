import { Typography } from "@/components/NouiTypography";
import { useSidebarStatus } from "@/hooks/useSidebarStatus";
import { cn } from "@/lib/utils";
import { useI18n } from "@/i18n";

export function SidebarFooter() {
  const status = useSidebarStatus();
  const { t } = useI18n();

  return (
    <div
      className={cn(
        "flex shrink-0 items-center justify-between gap-2",
        "px-5 py-2.5",
        "border-t border-[var(--studio-border-subtle)]",
      )}
    >
      <Typography
        className="font-mono-ui text-[0.72rem] tabular-nums tracking-normal text-[var(--studio-text-soft)] lowercase"
      >
        {status?.version != null ? `v${status.version}` : "—"}
      </Typography>

      <a
        href="https://nousresearch.com"
        target="_blank"
        rel="noopener noreferrer"
        className={cn(
          "text-[0.72rem] font-medium tracking-normal text-[var(--studio-text-soft)]",
          "transition-colors hover:text-[var(--studio-text)]",
          "focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-teal-700/40",
        )}
      >
        {t.app.footer.org}
      </a>
    </div>
  );
}
