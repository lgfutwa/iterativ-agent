# Iterativ for iOS

This is a native SwiftUI companion app for Iterativ. iOS cannot launch the
local Python dashboard process directly, so the app connects to an Iterativ
dashboard URL that is already running on a Mac or reachable server.

## Build

```bash
apps/ios/IterativIOS/Scripts/build_app.sh
```

The script builds an unsigned simulator app and copies it to:

```text
apps/ios/IterativIOS/build/IterativIOS.app
```

## Run

Start the dashboard on the Mac:

```bash
iterativ dashboard --tui --host 127.0.0.1 --port 9119
```

Then install the app on a booted simulator:

```bash
xcrun simctl install booted apps/ios/IterativIOS/build/IterativIOS.app
xcrun simctl launch booted ai.iterativ.ios
```

The default dashboard URL is `http://127.0.0.1:9119`. For a physical iPhone or
iPad, use the Mac's LAN address instead, for example `http://192.168.1.42:9119`.
The dashboard must be started with a host that the device can reach.
