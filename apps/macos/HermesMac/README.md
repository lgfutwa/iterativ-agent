# Hermes for macOS

This is a native SwiftUI shell for Hermes. It launches the local Hermes
dashboard with the embedded TUI enabled, renders it in a `WKWebView`, and owns
the local server lifecycle while the window is open.

## Build

```bash
apps/macos/HermesMac/Scripts/build_app.sh
```

The built app is written to:

```text
apps/macos/HermesMac/build/Hermes.app
```

Run it from this checkout with:

```bash
open apps/macos/HermesMac/build/Hermes.app
```

The app searches upward from its working directory and bundle location for a
Hermes checkout. In a source checkout it prefers `.venv/bin/python3`, then
`venv/bin/python3`, before falling back to the executable `hermes` launcher.
If no checkout is found, it runs `hermes` from `PATH`.

If you move `Hermes.app` outside the checkout, either install `hermes` on your
`PATH` or set `HERMES_REPO_ROOT` for GUI apps:

```bash
launchctl setenv HERMES_REPO_ROOT /path/to/hermes-agent
open /path/to/Hermes.app
```

## Runtime Notes

- The app binds the dashboard to `127.0.0.1` and tries ports `9119...9149`.
- It starts Hermes with `dashboard --no-open --tui`.
- Closing the app terminates the child dashboard process it started.
- The first dashboard launch may build the web assets if they are not already
  present.
