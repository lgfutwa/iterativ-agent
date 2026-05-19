#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$APP_ROOT/../../.." && pwd)"
CONFIGURATION="${CONFIGURATION:-release}"
PRODUCT_NAME="Hermes"
BUNDLE_ID="${BUNDLE_ID:-ai.hermes.mac}"
BUILD_ROOT="$APP_ROOT/build"
APP_BUNDLE="$BUILD_ROOT/$PRODUCT_NAME.app"
SWIFTPM_SUPPORT="$APP_ROOT/.build/swiftpm-support"
CLANG_MODULE_CACHE_PATH="$APP_ROOT/.build/clang-module-cache"

export CLANG_MODULE_CACHE_PATH
mkdir -p \
  "$SWIFTPM_SUPPORT/cache" \
  "$SWIFTPM_SUPPORT/config" \
  "$SWIFTPM_SUPPORT/security" \
  "$CLANG_MODULE_CACHE_PATH"

swift build \
  --package-path "$APP_ROOT" \
  --scratch-path "$APP_ROOT/.build" \
  --cache-path "$SWIFTPM_SUPPORT/cache" \
  --config-path "$SWIFTPM_SUPPORT/config" \
  --security-path "$SWIFTPM_SUPPORT/security" \
  -c "$CONFIGURATION"

EXECUTABLE="$APP_ROOT/.build/$CONFIGURATION/HermesMac"

rm -rf "$APP_BUNDLE"
mkdir -p "$APP_BUNDLE/Contents/MacOS" "$APP_BUNDLE/Contents/Resources"
cp "$EXECUTABLE" "$APP_BUNDLE/Contents/MacOS/$PRODUCT_NAME"

cat > "$APP_BUNDLE/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleDisplayName</key>
  <string>Hermes</string>
  <key>CFBundleExecutable</key>
  <string>$PRODUCT_NAME</string>
  <key>CFBundleIdentifier</key>
  <string>$BUNDLE_ID</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>Hermes</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>0.1.0</string>
  <key>CFBundleVersion</key>
  <string>1</string>
  <key>LSMinimumSystemVersion</key>
  <string>13.0</string>
  <key>NSAppTransportSecurity</key>
  <dict>
    <key>NSAllowsLocalNetworking</key>
    <true/>
  </dict>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>NSPrincipalClass</key>
  <string>NSApplication</string>
</dict>
</plist>
PLIST

printf 'APPL????' > "$APP_BUNDLE/Contents/PkgInfo"

echo "Built $APP_BUNDLE"
echo "Run with: open \"$APP_BUNDLE\""
echo "Detected checkout root: $REPO_ROOT"
