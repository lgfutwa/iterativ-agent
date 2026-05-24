declare global {
  interface Window {
    /** Set true by the server only for `iterativ dashboard --tui` (or ITERATIV_DASHBOARD_TUI=1). */
    __ITERATIV_DASHBOARD_EMBEDDED_CHAT__?: boolean;
    /** @deprecated Older injected name; treated as on when true. */
    __ITERATIV_DASHBOARD_TUI__?: boolean;
    /** @deprecated Legacy Hermes name; treated as on when true. */
    __HERMES_DASHBOARD_EMBEDDED_CHAT__?: boolean;
    /** @deprecated Legacy Hermes name; treated as on when true. */
    __HERMES_DASHBOARD_TUI__?: boolean;
  }
}

/** True only when the dashboard was started with embedded TUI Chat (`iterativ dashboard --tui`). */
export function isDashboardEmbeddedChatEnabled(): boolean {
  if (typeof window === "undefined") return false;
  if (window.__ITERATIV_DASHBOARD_EMBEDDED_CHAT__ === true) return true;
  if (window.__ITERATIV_DASHBOARD_TUI__ === true) return true;
  if (window.__HERMES_DASHBOARD_EMBEDDED_CHAT__ === true) return true;
  return window.__HERMES_DASHBOARD_TUI__ === true;
}
