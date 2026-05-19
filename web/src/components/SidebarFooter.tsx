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
        "border-t border-stone-100",
      )}
    >
      <Typography
        className="font-mono-ui text-[0.72rem] tabular-nums tracking-normal text-stone-500 lowercase"
      >
        {status?.version != null ? `v${status.version}` : "—"}
      </Typography>

      <a
        href="https://nousresearch.com"
        target="_blank"
        rel="noopener noreferrer"
        className={cn(
          "text-[0.72rem] font-medium tracking-normal text-stone-500",
          "transition-colors hover:text-stone-950",
          "focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-teal-700/40",
        )}
      >
        {t.app.footer.org}
      </a>
    </div>
  );
}
