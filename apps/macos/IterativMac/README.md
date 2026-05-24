# Iterativ for macOS

This is a native SwiftUI shell for Iterativ. It launches the local Iterativ
agent and provides a menu bar interface for starting/stopping the gateway,
viewing logs, and opening the dashboard.

## Build

```bash
apps/macos/IterativMac/Scripts/build_app.sh
```

The built app is written to:

```text
apps/macos/IterativMac/build/Iterativ.app
```

Run it from this checkout with:

```bash
open apps/macos/IterativMac/build/Iterativ.app
```

The app searches upward from its working directory and bundle location for a
Iterativ checkout. In a source checkout it prefers `.venv/bin/python3`, then
`venv/bin/python3`, before falling back to the executable `iterativ` launcher.
If no checkout is found, it runs `iterativ` from `PATH`.

If you move `Iterativ.app` outside the checkout, either install `iterativ` on your
`PATH` or set `ITERATIV_REPO_ROOT` for GUI apps:

```bash
launchctl setenv ITERATIV_REPO_ROOT /path/to/iterativ-agent
open /path/to/Iterativ.app
```

## Runtime Notes

- The app binds the dashboard to `127.0.0.1` and tries ports `9119...9149`.
- It starts Iterativ with `dashboard --no-open --tui`.
- Closing the app terminates the child dashboard process it started.
- The first dashboard launch may build the web assets if they are not already
  present.
