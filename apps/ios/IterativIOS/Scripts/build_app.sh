#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="$APP_ROOT/IterativIOS.xcodeproj"
SCHEME="IterativIOS"
CONFIGURATION="${CONFIGURATION:-Debug}"
BUILD_ROOT="$APP_ROOT/build"
DERIVED_DATA="$BUILD_ROOT/DerivedData"
PRODUCT_DIR="$DERIVED_DATA/Build/Products/$CONFIGURATION-iphonesimulator"
APP_BUNDLE="$PRODUCT_DIR/$SCHEME.app"
OUTPUT_BUNDLE="$BUILD_ROOT/$SCHEME.app"

mkdir -p "$BUILD_ROOT"

xcodebuild \
  -project "$PROJECT" \
  -scheme "$SCHEME" \
  -configuration "$CONFIGURATION" \
  -sdk iphonesimulator \
  -destination "generic/platform=iOS Simulator" \
  -derivedDataPath "$DERIVED_DATA" \
  CODE_SIGNING_ALLOWED=NO \
  build

rm -rf "$OUTPUT_BUNDLE"
cp -R "$APP_BUNDLE" "$OUTPUT_BUNDLE"

echo "Built $OUTPUT_BUNDLE"
echo "Install on a booted simulator with:"
echo "  xcrun simctl install booted \"$OUTPUT_BUNDLE\""
