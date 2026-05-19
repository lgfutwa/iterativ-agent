import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Bot,
  CheckCircle2,
  Code2,
  Globe2,
  Mic,
  MonitorCog,
  Paperclip,
  Radar,
  Search,
  Settings,
  Sparkles,
  Terminal,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@nous-research/ui/ui/components/button";
import { Spinner } from "@nous-research/ui/ui/components/spinner";
import { api, type SessionInfo, type StatusResponse } from "@/lib/api";
import { isDashboardEmbeddedChatEnabled } from "@/lib/dashboard-flags";
import { cn, timeAgo } from "@/lib/utils";
import { PluginSlot } from "@/plugins";

const STARTERS = [
  {
    icon: Search,
    title: "Research a decision",
    prompt:
      "Research the best current options, compare tradeoffs, cite sources, and give me a recommendation.",
  },
  {
    icon: Code2,
    title: "Build a feature",
    prompt:
      "Build the requested feature end to end, run the relevant checks, and summarize what changed.",
  },
  {
    icon: Radar,
    title: "Monitor changes",
    prompt:
      "Set up a recurring monitor for this target, report meaningful changes, and avoid noisy updates.",
  },
  {
    icon: Globe2,
    title: "Browse a site",
    prompt:
      "Use the browser to inspect the site, extract the important details, and turn them into a concise brief.",
  },
];

const LUCKY_PROMPT =
  "Look at this workspace, suggest three useful next moves, and start with the highest-impact one.";

export default function ComputerPage() {
  const navigate = useNavigate();
  const embeddedChat = isDashboardEmbeddedChatEnabled();
  const [prompt, setPrompt] = useState("");
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    Promise.allSettled([api.getStatus(), api.getSessions(6, 0)]).then(
      ([statusResult, sessionsResult]) => {
        if (cancelled) return;
        if (statusResult.status === "fulfilled") setStatus(statusResult.value);
        if (sessionsResult.status === "fulfilled") {
          setSessions(sessionsResult.value.sessions);
        }
        setLoading(false);
      },
    );

    return () => {
      cancelled = true;
    };
  }, []);

  const activeSessions = status?.active_sessions ?? 0;
  const gatewayState = useMemo(() => {
    if (!status) return { label: "Checking", tone: "text-muted-foreground" };
    if (status.gateway_state === "running" || status.gateway_running) {
      return { label: "Online", tone: "text-[var(--studio-success)]" };
    }
    if (status.gateway_state === "starting") {
      return { label: "Starting", tone: "text-[var(--studio-warning)]" };
    }
    if (status.gateway_state === "startup_failed") {
      return { label: "Attention", tone: "text-[var(--studio-danger)]" };
    }
    return { label: "Local", tone: "text-[var(--studio-text-muted)]" };
  }, [status]);

  const workspaceLabel = embeddedChat ? "Workspace ready" : "Dashboard mode";
  const recentSessions = sessions.slice(0, 4);

  const launchComputer = (nextPrompt = prompt) => {
    const clean = nextPrompt.trim();
    if (!embeddedChat) {
      navigate("/sessions");
      return;
    }

    const qs = new URLSearchParams();
    if (clean) qs.set("prompt", clean);
    navigate(`/chat${qs.size ? `?${qs.toString()}` : ""}`);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    launchComputer();
  };

  return (
    <div className="computer-page flex min-h-full w-full flex-1 flex-col px-4 py-3 sm:px-6 lg:px-8">
      <PluginSlot name="computer:top" />

      <div className="mx-auto flex w-full max-w-[1160px] flex-1 flex-col">
        <div className="flex h-12 shrink-0 items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => navigate("/sessions")}
            className="studio-pill max-w-[68vw] px-3 py-1.5 text-left text-xs font-medium sm:max-w-none"
          >
            {loading ? (
              <Spinner className="studio-soft-copy" />
            ) : (
              <span
                className={cn(
                  "h-2 w-2 shrink-0 rounded-full",
                  gatewayState.label === "Online"
                    ? "bg-[var(--studio-success)]"
                    : gatewayState.label === "Attention"
                      ? "bg-[var(--studio-danger)]"
                      : "bg-[var(--studio-warning)]",
                )}
              />
            )}
            <span className="truncate">{workspaceLabel}</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => navigate("/config")}
              title="Settings"
              aria-label="Settings"
              className="studio-icon-button"
            >
              <Settings className="h-4 w-4" />
            </button>
          </div>
        </div>

        <section className="flex flex-1 flex-col items-center justify-center pb-10 pt-8 text-center sm:pt-12 lg:pb-16">
          <div className="studio-muted-copy mb-7 flex items-center gap-3 text-sm font-medium">
            <span className="studio-brand-mark inline-flex h-9 w-9 items-center justify-center rounded-full">
              <Sparkles className="h-4 w-4" />
            </span>
            <span>Iterativ Computer</span>
          </div>

          <h1 className="max-w-3xl text-balance font-sans text-4xl font-normal leading-tight tracking-normal text-[var(--studio-text)] sm:text-5xl lg:text-[3.5rem]">
            What should Iterativ do?
          </h1>

          <form
            onSubmit={handleSubmit}
            className="computer-composer-shell mt-9 w-full max-w-[980px] text-left"
          >
            <div className="computer-composer-inner">
              <textarea
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    launchComputer();
                  }
                }}
                rows={4}
                placeholder="Ask Iterativ to research, browse, build, monitor, or operate your tools..."
                className="min-h-32 w-full resize-none border-0 bg-transparent px-5 py-5 font-sans text-base leading-relaxed text-[var(--studio-text)] outline-none placeholder:text-[var(--studio-text-muted)]"
              />

              <div className="flex flex-col gap-3 px-4 pb-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    title="Voice prompt"
                    aria-label="Voice prompt"
                    className="studio-icon-button"
                  >
                    <Mic className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    title="Attach context"
                    aria-label="Attach context"
                    className="studio-icon-button"
                  >
                    <Paperclip className="h-4 w-4" />
                  </button>
                  <span className="studio-soft-copy hidden items-center gap-2 pl-2 text-xs md:inline-flex">
                    <Terminal className="h-3.5 w-3.5" />
                    {embeddedChat
                      ? "Live workspace"
                      : "Local workspace"}
                  </span>
                </div>

                <div className="flex flex-wrap items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => launchComputer(LUCKY_PROMPT)}
                    className="studio-secondary-action h-9 px-3 text-sm font-medium"
                  >
                    <Sparkles className="studio-interactive-blue h-4 w-4" />
                    <span className="hidden sm:inline">I'm feeling lucky</span>
                  </button>

                  <Button
                    type="submit"
                    className="studio-primary-action h-9 px-4 font-sans text-sm tracking-normal"
                  >
                    <span className="inline-flex items-center gap-2 normal-case">
                      Start
                      <ArrowRight className="h-4 w-4" />
                    </span>
                  </Button>
                </div>
              </div>
            </div>
          </form>

          <div className="mt-6 flex w-full max-w-[980px] flex-wrap justify-center gap-2">
            {STARTERS.map(({ icon: Icon, title, prompt: starterPrompt }) => (
              <button
                key={title}
                type="button"
                onClick={() => launchComputer(starterPrompt)}
                className="studio-chip group px-4 py-2 text-sm font-medium"
              >
                <Icon className="studio-interactive-blue h-4 w-4 shrink-0" />
                <span className="truncate">{title}</span>
              </button>
            ))}
          </div>

          <div className="mt-9 flex flex-wrap items-center justify-center gap-2 text-xs text-gray-500">
            <StatusBadge
              icon={MonitorCog}
              label="Gateway"
              value={gatewayState.label}
              valueClassName={gatewayState.tone}
            />
            <StatusBadge
              icon={Bot}
              label="Active sessions"
              value={String(activeSessions)}
            />
            <StatusBadge
              icon={CheckCircle2}
              label="Version"
              value={status?.version ?? "unknown"}
            />
          </div>
        </section>

        {recentSessions.length > 0 && (
          <section className="mx-auto mb-7 w-full max-w-[980px]">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h2 className="text-sm font-semibold text-[var(--studio-text)]">Recent work</h2>
              <button
                type="button"
                onClick={() => navigate("/sessions")}
                className="studio-muted-copy text-sm font-medium transition hover:text-[var(--studio-text)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--studio-focus)]/30"
              >
                View all
              </button>
            </div>

            <div className="grid gap-2 md:grid-cols-2">
              {recentSessions.map((session) => (
                <button
                  key={session.id}
                  type="button"
                  onClick={() =>
                    embeddedChat
                      ? navigate(`/chat?resume=${encodeURIComponent(session.id)}`)
                      : navigate("/sessions")
                  }
                  className="group rounded-[var(--studio-radius-sm)] border border-[var(--studio-border-subtle)] bg-[var(--studio-surface-raised)] px-3 py-3 text-left shadow-sm transition hover:border-[color-mix(in_srgb,var(--studio-blue)_22%,var(--studio-border))] hover:bg-[color-mix(in_srgb,var(--studio-blue-soft)_42%,white)]"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="min-w-0 truncate text-sm font-medium text-[var(--studio-text)]">
                      {session.title || session.preview || "Untitled session"}
                    </p>
                    <ArrowRight className="h-3.5 w-3.5 shrink-0 text-[var(--studio-text-soft)] group-hover:text-[var(--studio-blue)]" />
                  </div>
                  <p className="studio-muted-copy mt-1 truncate text-xs">
                    {session.model || session.source || "Iterativ"} · {timeAgo(session.last_active)}
                  </p>
                </button>
              ))}
            </div>
          </section>
        )}
      </div>

      <PluginSlot name="computer:bottom" />
    </div>
  );
}

function StatusBadge({
  icon: Icon,
  label,
  value,
  valueClassName,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  valueClassName?: string;
}) {
  return (
    <span className="studio-status-pill max-w-full rounded-full px-3 py-1.5">
      <Icon className="h-3.5 w-3.5 shrink-0 text-[var(--studio-text-soft)]" />
      <span className="truncate text-[var(--studio-text-muted)]">{label}</span>
      <span
        className={cn(
          "max-w-[10rem] truncate font-medium text-[var(--studio-text)]",
          valueClassName,
        )}
      >
        {value}
      </span>
    </span>
  );
}
