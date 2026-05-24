import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ComponentType,
  type ReactNode,
} from "react";
import {
  Routes,
  Route,
  NavLink,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";
import {
  Activity,
  BarChart3,
  BookOpen,
  Brain,
  Clock,
  Cloud,
  Code,
  Cpu,
  Database,
  Download,
  Eye,
  FileText,
  FolderOpen,
  Globe,
  GitBranch,
  Heart,
  KeyRound,
  Menu,
  MessageSquare,
  MonitorCog,
  Package,
  Plus,
  Puzzle,
  RotateCw,
  Search,
  Settings,
  Shield,
  Sparkles,
  Star,
  Terminal,
  Users,
  Wrench,
  X,
  Zap,
} from "lucide-react";
import { Button } from "@nous-research/ui/ui/components/button";
import { ListItem } from "@nous-research/ui/ui/components/list-item";
import { SelectionSwitcher } from "@nous-research/ui/ui/components/selection-switcher";
import { Spinner } from "@nous-research/ui/ui/components/spinner";
import { Typography } from "@/components/NouiTypography";
import { cn } from "@/lib/utils";
import { SidebarFooter } from "@/components/SidebarFooter";
import { SidebarStatusStrip } from "@/components/SidebarStatusStrip";
import { PageHeaderProvider } from "@/contexts/PageHeaderProvider";
import { useSystemActions } from "@/contexts/useSystemActions";
import type { SystemAction } from "@/contexts/system-actions-context";
import ConfigPage from "@/pages/ConfigPage";
import DocsPage from "@/pages/DocsPage";
import EnvPage from "@/pages/EnvPage";
import SessionsPage from "@/pages/SessionsPage";
import LogsPage from "@/pages/LogsPage";
import AnalyticsPage from "@/pages/AnalyticsPage";
import ModelsPage from "@/pages/ModelsPage";
import CronPage from "@/pages/CronPage";
import ProfilesPage from "@/pages/ProfilesPage";
import SkillsPage from "@/pages/SkillsPage";
import PluginsPage from "@/pages/PluginsPage";
import ChatPage from "@/pages/ChatPage";
import ComputerPage from "@/pages/ComputerPage";
import MultiModelPage from "@/pages/MultiModelPage";
import WorkflowPage from "@/pages/WorkflowPage";
import SetupWizard from "@/pages/SetupWizard";
import CloudPage from "@/pages/CloudPage";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import { useI18n } from "@/i18n";
import type { Translations } from "@/i18n/types";
import { PluginPage, PluginSlot, usePlugins } from "@/plugins";
import type { PluginManifest } from "@/plugins";
import { useTheme } from "@/themes";
import { isDashboardEmbeddedChatEnabled } from "@/lib/dashboard-flags";
import { api } from "@/lib/api";

function RootRedirect() {
  return <Navigate to="/computer" replace />;
}

function UnknownRouteFallback({ pluginsLoading }: { pluginsLoading: boolean }) {
  if (pluginsLoading) {
    // Render nothing during the plugin-load window — a spinner here would just flash.
    return null;
  }
  return <Navigate to="/computer" replace />;
}

const CHAT_NAV_ITEM: NavItem = {
  path: "/chat",
  label: "Workspace",
  icon: Terminal,
};

/**
 * Built-in routes except /chat.  Chat is rendered persistently (outside
 * <Routes>) when embedded — see the persistent chat host block rendered
 * inline near the bottom of this file — so the PTY child, WebSocket,
 * and xterm instance survive when the user visits another tab and comes
 * back.  A `display:none` toggle hides the terminal without unmounting.
 * Routing still owns the URL so /chat deep-links, browser back/forward,
 * and nav highlight keep working.
 */
const BUILTIN_ROUTES_CORE: Record<string, ComponentType> = {
  "/": RootRedirect,
  "/computer": ComputerPage,
  "/sessions": SessionsPage,
  "/analytics": AnalyticsPage,
  "/models": ModelsPage,
  "/multimodel": MultiModelPage,
  "/workflows": WorkflowPage,
  "/cloud": CloudPage,
  "/setup": SetupWizard,
  "/logs": LogsPage,
  "/cron": CronPage,
  "/skills": SkillsPage,
  "/plugins": PluginsPage,
  "/profiles": ProfilesPage,
  "/config": ConfigPage,
  "/env": EnvPage,
  "/docs": DocsPage,
};

// Route placeholder for /chat.  The persistent ChatPage host (rendered
// outside <Routes> when embedded chat is on) paints on top; this empty
// element just claims the path so the `*` catch-all redirect doesn't
// fire when the user navigates to /chat.
function ChatRouteSink() {
  return null;
}

const BUILTIN_NAV_REST: NavItem[] = [
  {
    path: "/computer",
    label: "Computer",
    icon: MonitorCog,
  },
  {
    path: "/sessions",
    labelKey: "sessions",
    label: "Sessions",
    icon: MessageSquare,
  },
  {
    path: "/analytics",
    labelKey: "analytics",
    label: "Analytics",
    icon: BarChart3,
  },
  {
    path: "/models",
    labelKey: "models",
    label: "Models",
    icon: Cpu,
  },
  {
    path: "/multimodel",
    labelKey: "multimodel",
    label: "Multi-Model",
    icon: Brain,
  },
  {
    path: "/workflows",
    labelKey: "workflows",
    label: "Workflows",
    icon: GitBranch,
  },
  {
    path: "/cloud",
    labelKey: "cloud",
    label: "Cloud",
    icon: Cloud,
  },
  {
    path: "/logs",
    labelKey: "logs",
    label: "Logs",
    icon: FileText,
  },
  {
    path: "/cron",
    labelKey: "cron",
    label: "Cron",
    icon: Clock,
  },
  {
    path: "/skills",
    labelKey: "skills",
    label: "Skills",
    icon: Puzzle,
  },
  {
    path: "/plugins",
    labelKey: "plugins",
    label: "Plugins",
    icon: Package,
  },
  {
    path: "/profiles",
    labelKey: "profiles",
    label: "Profiles",
    icon: Users,
  },
  {
    path: "/config",
    labelKey: "config",
    label: "Config",
    icon: Settings,
  },
  {
    path: "/env",
    labelKey: "env",
    label: "Environment",
    icon: KeyRound,
  },
  {
    path: "/docs",
    labelKey: "docs",
    label: "Docs",
    icon: BookOpen,
  },
];

const ICON_MAP: Record<string, ComponentType<{ className?: string }>> = {
  Activity,
  BarChart3,
  Clock,
  Cpu,
  FileText,
  KeyRound,
  MessageSquare,
  Package,
  Settings,
  Puzzle,
  Sparkles,
  Terminal,
  Globe,
  Database,
  Shield,
  Users,
  Wrench,
  Zap,
  Heart,
  Star,
  Code,
  Eye,
  MonitorCog,
};

function resolveIcon(name: string): ComponentType<{ className?: string }> {
  return ICON_MAP[name] ?? Puzzle;
}

function buildNavItems(
  builtIn: NavItem[],
  manifests: PluginManifest[],
): NavItem[] {
  const items = [...builtIn];

  for (const manifest of manifests) {
    if (manifest.tab.override) continue;
    if (manifest.tab.hidden) continue;

    const pluginItem: NavItem = {
      path: manifest.tab.path,
      label: manifest.label,
      icon: resolveIcon(manifest.icon),
    };

    const pos = manifest.tab.position ?? "end";
    if (pos === "end") {
      items.push(pluginItem);
    } else if (pos.startsWith("after:")) {
      const target = "/" + pos.slice(6);
      const idx = items.findIndex((i) => i.path === target);
      items.splice(idx >= 0 ? idx + 1 : items.length, 0, pluginItem);
    } else if (pos.startsWith("before:")) {
      const target = "/" + pos.slice(7);
      const idx = items.findIndex((i) => i.path === target);
      items.splice(idx >= 0 ? idx : items.length, 0, pluginItem);
    } else {
      items.push(pluginItem);
    }
  }

  return items;
}

/** Split merged nav into built-in sidebar entries vs plugin tabs, preserving plugin order hints. */
function partitionSidebarNav(
  builtIn: NavItem[],
  manifests: PluginManifest[],
): { coreItems: NavItem[]; pluginItems: NavItem[] } {
  const merged = buildNavItems(builtIn, manifests);
  const builtinPaths = new Set(builtIn.map((i) => i.path));
  const coreItems: NavItem[] = [];
  const pluginItems: NavItem[] = [];
  for (const item of merged) {
    if (builtinPaths.has(item.path)) coreItems.push(item);
    else pluginItems.push(item);
  }
  return { coreItems, pluginItems };
}

function buildRoutes(
  builtinRoutes: Record<string, ComponentType>,
  manifests: PluginManifest[],
): Array<{
  key: string;
  path: string;
  element: ReactNode;
}> {
  const byOverride = new Map<string, PluginManifest>();
  const addons: PluginManifest[] = [];

  for (const m of manifests) {
    if (m.tab.override) {
      byOverride.set(m.tab.override, m);
    } else {
      addons.push(m);
    }
  }

  const routes: Array<{
    key: string;
    path: string;
    element: ReactNode;
  }> = [];

  for (const [path, Component] of Object.entries(builtinRoutes)) {
    const om = byOverride.get(path);
    if (om) {
      routes.push({
        key: `override:${om.name}`,
        path,
        element: <PluginPage name={om.name} />,
      });
    } else {
      routes.push({ key: `builtin:${path}`, path, element: <Component /> });
    }
  }

  for (const m of addons) {
    if (m.tab.hidden) continue;
    if (m.tab.path === "/plugins") continue;
    if (builtinRoutes[m.tab.path]) continue;
    routes.push({
      key: `plugin:${m.name}`,
      path: m.tab.path,
      element: <PluginPage name={m.name} />,
    });
  }

  for (const m of manifests) {
    if (!m.tab.hidden) continue;
    if (m.tab.path === "/plugins") continue;
    if (builtinRoutes[m.tab.path] || m.tab.override) continue;
    routes.push({
      key: `plugin:hidden:${m.name}`,
      path: m.tab.path,
      element: <PluginPage name={m.name} />,
    });
  }

  return routes;
}

export default function App() {
  const { t } = useI18n();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { manifests, loading: pluginsLoading } = usePlugins();
  const { theme } = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);
  const closeMobile = useCallback(() => setMobileOpen(false), []);
  const startNewThread = useCallback(() => {
    navigate(`/chat?thread=${Date.now().toString(36)}`);
    closeMobile();
  }, [closeMobile, navigate]);
  const isDocsRoute = pathname === "/docs" || pathname === "/docs/";
  const normalizedPath = pathname.replace(/\/$/, "") || "/";
  const isChatRoute = normalizedPath === "/chat";
  const embeddedChat = isDashboardEmbeddedChatEnabled();

  // `dashboard.show_token_analytics` gates the Analytics nav item.  The
  // page itself remains reachable by URL (it renders an explanation when
  // the flag is off — see AnalyticsPage), but hiding the nav entry avoids
  // surfacing misleading token/cost numbers in the sidebar.  Default off.
  const [showTokenAnalytics, setShowTokenAnalytics] = useState(false);
  useEffect(() => {
    api
      .getConfig()
      .then((cfg) => {
        const dash = (cfg?.dashboard ?? {}) as { show_token_analytics?: unknown };
        setShowTokenAnalytics(dash.show_token_analytics === true);
      })
      .catch(() => setShowTokenAnalytics(false));
  }, []);

  // A plugin can replace the built-in /chat page via `tab.override: "/chat"`
  // in its manifest.  When one does, `buildRoutes` already swaps the route
  // element for <PluginPage /> — but we also have to suppress the
  // persistent ChatPage host below, or the plugin's page and the built-in
  // terminal would paint on top of each other.  The override is niche
  // (nothing ships overriding /chat today) but it's an advertised
  // extension point, so preserve the pre-persistence contract: when a
  // plugin owns /chat, the built-in chat UI is entirely absent.
  //
  // Waiting on `pluginsLoading` is load-bearing: manifests arrive
  // asynchronously from /api/dashboard/plugins, so on initial render
  // `chatOverriddenByPlugin` is always false.  Without the loading
  // gate, the persistent host would mount, spawn a PTY, and THEN get
  // yanked out from under the user when the plugin's manifest resolves
  // — killing the session mid-paint.  Delaying host mount by the
  // plugin-load window (typically <50ms, worst case 2s safety timeout)
  // is the cheaper trade-off.
  const chatOverriddenByPlugin = useMemo(
    () => manifests.some((m) => m.tab.override === "/chat"),
    [manifests],
  );

  const builtinRoutes = useMemo(
    () => ({
      ...BUILTIN_ROUTES_CORE,
      ...(embeddedChat ? { "/chat": ChatRouteSink } : {}),
    }),
    [embeddedChat],
  );

  const builtinNav = useMemo(() => {
    const base = embeddedChat
      ? [CHAT_NAV_ITEM, ...BUILTIN_NAV_REST]
      : BUILTIN_NAV_REST;
    return showTokenAnalytics ? base : base.filter((n) => n.path !== "/analytics");
  }, [embeddedChat, showTokenAnalytics]);

  const sidebarNav = useMemo(
    () => partitionSidebarNav(builtinNav, manifests),
    [builtinNav, manifests],
  );
  const routes = useMemo(
    () => buildRoutes(builtinRoutes, manifests),
    [builtinRoutes, manifests],
  );
  const pluginTabMeta = useMemo(
    () =>
      manifests
        .filter((m) => !m.tab.hidden)
        .map((m) => ({
          path: m.tab.override ?? m.tab.path,
          label: m.label,
        })),
    [manifests],
  );

  const layoutVariant = theme.layoutVariant ?? "standard";

  useEffect(() => {
    if (!mobileOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileOpen(false);
    };
    document.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [mobileOpen]);

  useEffect(() => {
    const mql = window.matchMedia("(min-width: 1024px)");
    const onChange = (e: MediaQueryListEvent) => {
      if (e.matches) setMobileOpen(false);
    };
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return (
    <div
      data-layout-variant={layoutVariant}
      className="computer-ui-shell flex h-dvh max-h-dvh min-h-0 flex-col overflow-hidden bg-[var(--studio-app-bg)] font-sans text-[var(--studio-text)] antialiased"
    >
      <SelectionSwitcher />
      <PluginSlot name="backdrop" />

      <header
        className={cn(
          "lg:hidden fixed top-0 left-0 right-0 z-40 min-h-14",
          "flex items-center gap-2 px-4 py-2",
          "border-b border-[var(--studio-border-subtle)]",
          "bg-[var(--studio-surface)]/95 backdrop-blur-sm",
        )}
        style={{
          background: "var(--component-header-background)",
          borderImage: "var(--component-header-border-image)",
          clipPath: "var(--component-header-clip-path)",
        }}
      >
        <Button
          ghost
          size="icon"
          onClick={() => setMobileOpen(true)}
          aria-label={t.app.openNavigation}
          aria-expanded={mobileOpen}
          aria-controls="app-sidebar"
          className="text-[var(--studio-text-muted)] hover:text-[var(--studio-text)]"
        >
          <Menu />
        </Button>

        <Typography
          className="font-sans text-[0.95rem] font-semibold leading-[1] tracking-normal text-[var(--studio-text)]"
        >
          Iterativ Studio
        </Typography>
      </header>

      {mobileOpen && (
        <Button
          ghost
          aria-label={t.app.closeNavigation}
          onClick={closeMobile}
          className={cn(
            "lg:hidden fixed inset-0 z-40 p-0 block",
            "bg-black/60 backdrop-blur-sm",
          )}
        />
      )}

      <PluginSlot name="header-banner" />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden pt-14 lg:pt-0">
        <div className="flex min-h-0 min-w-0 flex-1">
          <aside
            id="app-sidebar"
            aria-label={t.app.navigation}
            className={cn(
              "computer-sidebar fixed top-0 left-0 z-50 flex h-dvh max-h-dvh w-[19rem] min-h-0 flex-col",
              "border border-[var(--studio-border-subtle)]",
              "bg-[var(--studio-sidebar-bg)] backdrop-blur-xl",
              "transition-transform duration-200 ease-out",
              mobileOpen ? "translate-x-0" : "-translate-x-full",
              "lg:sticky lg:top-0 lg:m-2 lg:h-[calc(100dvh-1rem)] lg:max-h-[calc(100dvh-1rem)] lg:translate-x-0 lg:shrink-0 lg:rounded-[24px]",
            )}
            style={{
              background:
                "var(--component-sidebar-background, var(--studio-sidebar-bg))",
              clipPath: "var(--component-sidebar-clip-path)",
              borderImage: "var(--component-sidebar-border-image)",
            }}
          >
            <div
              className={cn(
                "shrink-0 px-4 pb-4 pt-4",
              )}
            >
              <div className="mb-7 flex items-center justify-between gap-3">
                <div aria-hidden className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full bg-[#ff5f57]" />
                  <span className="h-3 w-3 rounded-full bg-[#ffbd2e]" />
                  <span className="h-3 w-3 rounded-full bg-[#28c840]" />
                </div>

                <Button
                  ghost
                  size="icon"
                  onClick={closeMobile}
                  aria-label={t.app.closeNavigation}
                  className="lg:hidden text-[var(--studio-text-muted)] hover:text-[var(--studio-text)]"
                >
                  <X />
                </Button>
              </div>

              <div
                className="mb-5 grid grid-cols-2 rounded-[22px] bg-[var(--studio-sidebar-segment)] p-1"
                aria-label={t.app.navigation}
              >
                <NavLink
                  to="/chat"
                  onClick={closeMobile}
                  title="Workspace"
                  aria-label="Workspace"
                  className={({ isActive }) =>
                    cn(
                      "flex h-10 items-center justify-center rounded-[18px] transition-colors",
                      "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--studio-focus)]",
                      isActive
                        ? "bg-[var(--studio-sidebar-segment-active)] text-[var(--studio-text)] shadow-sm"
                        : "text-[var(--studio-text-muted)] hover:text-[var(--studio-text)]",
                    )
                  }
                >
                  <Terminal className="h-4 w-4" />
                </NavLink>
                <NavLink
                  to="/computer"
                  onClick={closeMobile}
                  title="Computer"
                  aria-label="Computer"
                  className={({ isActive }) =>
                    cn(
                      "flex h-10 items-center justify-center rounded-[18px] transition-colors",
                      "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--studio-focus)]",
                      isActive
                        ? "bg-[var(--studio-sidebar-segment-active)] text-[var(--studio-text)] shadow-sm"
                        : "text-[var(--studio-text-muted)] hover:text-[var(--studio-text)]",
                    )
                  }
                >
                  <MonitorCog className="h-4 w-4" />
                </NavLink>
              </div>

              <div className="flex items-center gap-2">
                <PluginSlot name="header-left" />
                <Typography className="font-sans text-[0.95rem] font-semibold leading-[1.1] tracking-normal text-[var(--studio-text)]">
                  Iterativ Studio
                </Typography>
              </div>
            </div>

            <nav
              className="min-h-0 w-full flex-1 overflow-y-auto overflow-x-hidden px-2 pb-2"
              aria-label={t.app.navigation}
            >
              <div className="mb-2 flex flex-col gap-1.5 px-1">
                <button
                  type="button"
                  onClick={startNewThread}
                  className={cn(
                    "flex items-center gap-3 rounded-[12px] px-3 py-2.5 text-left",
                    "text-[0.9rem] font-medium tracking-normal text-[var(--studio-text)]",
                    "transition-colors hover:bg-white/65",
                    "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--studio-focus)]",
                  )}
                >
                  <Plus className="h-4 w-4 shrink-0" />
                  <span className="truncate">New Thread</span>
                </button>
                <NavLink
                  to="/workflows"
                  onClick={closeMobile}
                  className={cn(
                    "flex items-center gap-3 rounded-[12px] px-3 py-2.5",
                    "text-[0.9rem] font-medium tracking-normal text-[var(--studio-text)]",
                    "transition-colors hover:bg-white/65",
                    "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--studio-focus)]",
                  )}
                >
                  <FolderOpen className="h-4 w-4 shrink-0" />
                  <span className="truncate">Spaces</span>
                </NavLink>
                <div
                  aria-hidden
                  className="mt-3 flex h-10 items-center gap-2 rounded-[12px] border border-[var(--studio-border-subtle)] bg-white/45 px-3 text-[0.82rem] font-medium text-[var(--studio-text-muted)]"
                >
                  <Search className="h-4 w-4 shrink-0 opacity-55" />
                  <span className="truncate">AgentHire OS</span>
                </div>
              </div>

              <ul className="flex flex-col">
                {sidebarNav.coreItems.map((item) => (
                  <SidebarNavLink
                    closeMobile={closeMobile}
                    item={item}
                    key={item.path}
                    t={t}
                  />
                ))}
              </ul>

              {sidebarNav.pluginItems.length > 0 && (
                <div
                  aria-labelledby="iterativ-sidebar-plugin-nav-heading"
                  className="mt-2 flex flex-col border-t border-[var(--studio-border-subtle)] pb-2"
                  role="group"
                >
                  <span
                    className={cn(
                      "px-5 pt-2.5 pb-1",
                      "text-[0.68rem] font-medium tracking-normal text-[var(--studio-text-soft)]",
                    )}
                    id="iterativ-sidebar-plugin-nav-heading"
                  >
                    {t.app.pluginNavSection}
                  </span>

                  <ul className="flex flex-col">
                    {sidebarNav.pluginItems.map((item) => (
                      <SidebarNavLink
                        closeMobile={closeMobile}
                        item={item}
                        key={item.path}
                        t={t}
                      />
                    ))}
                  </ul>
                </div>
              )}
            </nav>

            <SidebarSystemActions onNavigate={closeMobile} />

            <div
              className={cn(
                "flex shrink-0 items-center justify-between gap-2",
                "px-3 py-2.5",
                "border-t border-[var(--studio-border-subtle)]",
              )}
            >
              <div className="flex min-w-0 items-center gap-2">
                <PluginSlot name="header-right" />
                <ThemeSwitcher dropUp />
                <LanguageSwitcher dropUp />
              </div>
            </div>

            <SidebarFooter />
          </aside>

          <PageHeaderProvider pluginTabs={pluginTabMeta}>
            <div
              className={cn(
                "relative z-2 flex min-w-0 min-h-0 flex-1 flex-col",
                "px-3 sm:px-6",
                isChatRoute
                  ? "pb-0 pt-1 sm:pt-2 lg:pt-4"
                  : normalizedPath === "/computer"
                    ? "px-0 pt-0 sm:px-0 sm:pt-0 lg:px-0 lg:pt-0"
                    : "pt-2 sm:pt-4 lg:pt-6",
                isDocsRoute && "min-h-0 flex-1",
              )}
            >
              <PluginSlot name="pre-main" />
              <div
                className={cn(
                  "w-full min-w-0",
                  !isChatRoute &&
                    "pb-[calc(2rem+env(safe-area-inset-bottom,0px))] lg:pb-8",
                  (isDocsRoute || isChatRoute) &&
                    "min-h-0 flex flex-1 flex-col",
                )}
              >
                <Routes>
                  {routes.map(({ key, path, element }) => (
                    <Route key={key} path={path} element={element} />
                  ))}
                  <Route
                    path="*"
                    element={
                      <UnknownRouteFallback pluginsLoading={pluginsLoading} />
                    }
                  />
                </Routes>

                {embeddedChat &&
                  !chatOverriddenByPlugin &&
                  (pluginsLoading ? (
                    isChatRoute ? (
                      <div
                        className="flex min-h-0 min-w-0 flex-1 items-center justify-center"
                        aria-busy="true"
                        aria-live="polite"
                      >
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Spinner />
                          <span>Loading chat…</span>
                        </div>
                      </div>
                    ) : null
                  ) : (
                    <div
                      data-chat-active={isChatRoute ? "true" : "false"}
                      className={cn(
                        "min-h-0 min-w-0",
                        isChatRoute ? "flex flex-1 flex-col" : "hidden",
                      )}
                      aria-hidden={!isChatRoute}
                    >
                      <ChatPage isActive={isChatRoute} />
                    </div>
                  ))}
              </div>
              <PluginSlot name="post-main" />
            </div>
          </PageHeaderProvider>
        </div>
      </div>

      <PluginSlot name="overlay" />
    </div>
  );
}

function SidebarNavLink({ closeMobile, item, t }: SidebarNavLinkProps) {
  const { path, label, labelKey, icon: Icon } = item;

  const navLabel = labelKey
    ? ((t.app.nav as Record<string, string>)[labelKey] ?? label)
    : label;

  return (
    <li>
      <NavLink
        to={path}
        end={path === "/sessions"}
        onClick={closeMobile}
        className={({ isActive }) =>
          cn(
            "group relative flex items-center gap-3",
            "rounded-[12px] px-3 py-2.5",
            "text-[0.9rem] font-medium tracking-normal",
            "whitespace-nowrap transition-colors cursor-pointer",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--studio-focus)]",
            isActive
              ? "bg-white/80 text-[var(--studio-text)] shadow-sm"
              : "text-[var(--studio-text-muted)] hover:bg-white/60 hover:text-[var(--studio-text)]",
          )
        }
        style={{
          clipPath: "var(--component-tab-clip-path)",
        }}
      >
        <Icon className="h-4 w-4 shrink-0" />
        <span className="truncate">{navLabel}</span>

        <span
          aria-hidden
          className="pointer-events-none absolute inset-y-0.5 left-1.5 right-1.5 opacity-0"
        />
      </NavLink>
    </li>
  );
}

function SidebarSystemActions({ onNavigate }: { onNavigate: () => void }) {
  const { t } = useI18n();
  const navigate = useNavigate();
  const { activeAction, isBusy, isRunning, pendingAction, runAction } =
    useSystemActions();

  const items: SystemActionItem[] = [
    {
      action: "restart",
      icon: RotateCw,
      label: t.status.restartGateway,
      runningLabel: t.status.restartingGateway,
      spin: true,
    },
    {
      action: "update",
      icon: Download,
      label: t.status.updateIterativ,
      runningLabel: t.status.updatingIterativ,
      spin: false,
    },
  ];

  const handleClick = (action: SystemAction) => {
    if (isBusy) return;
    void runAction(action);
    navigate("/sessions");
    onNavigate();
  };

  return (
    <div
      className={cn(
        "shrink-0 flex flex-col",
        "border-t border-[var(--studio-border-subtle)]",
        "px-2 py-2",
      )}
    >
      <span
        className={cn(
          "px-3 pt-0.5 pb-1",
          "text-[0.68rem] font-medium tracking-normal text-[var(--studio-text-soft)]",
        )}
      >
        {t.app.system}
      </span>

      <SidebarStatusStrip />

      <ul className="flex flex-col">
        {items.map(({ action, icon: Icon, label, runningLabel, spin }) => {
          const isPending = pendingAction === action;
          const isActionRunning =
            activeAction === action && isRunning && !isPending;
          const busy = isPending || isActionRunning;
          const displayLabel = isActionRunning ? runningLabel : label;
          const disabled = isBusy && !busy;

          return (
            <li key={action}>
              <ListItem
                onClick={() => handleClick(action)}
                disabled={disabled}
                aria-busy={busy}
                active={busy}
                className={cn(
                  "gap-3 rounded-[12px] px-3 py-2 whitespace-nowrap",
                  "text-[0.85rem] font-medium tracking-normal",
                  "transition-opacity",
                  busy
                    ? "bg-white/75 text-[var(--studio-text)] opacity-100 shadow-sm"
                    : "text-[var(--studio-text-muted)] opacity-100 hover:bg-white/55 hover:text-[var(--studio-text)]",
                  "disabled:opacity-30",
                )}
              >
                {isPending ? (
                  <Spinner className="shrink-0 text-[0.875rem]" />
                ) : isActionRunning && spin ? (
                  <Spinner className="shrink-0 text-[0.875rem]" />
                ) : (
                  <Icon
                    className={cn(
                      "h-4 w-4 shrink-0",
                      isActionRunning && !spin && "animate-pulse",
                    )}
                  />
                )}

                <span className="truncate">{displayLabel}</span>

                <span
                  aria-hidden
                  className="pointer-events-none absolute inset-y-0.5 left-1.5 right-1.5 opacity-0"
                />
              </ListItem>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

interface NavItem {
  icon: ComponentType<{ className?: string }>;
  label: string;
  labelKey?: string;
  path: string;
}

interface SidebarNavLinkProps {
  closeMobile: () => void;
  item: NavItem;
  t: Translations;
}

interface SystemActionItem {
  action: SystemAction;
  icon: ComponentType<{ className?: string }>;
  label: string;
  runningLabel: string;
  spin: boolean;
}
