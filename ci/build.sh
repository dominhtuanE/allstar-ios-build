#!/bin/bash
# Build target HelloJavascript-mobile (arm64, iOS 12+), khong ky; dong goi Payload/*.app -> out/AllstarShell.ipa
set -uo pipefail
ROOT="$(pwd)"
mkdir -p "$ROOT/out"
XPROJ="$ROOT/proj/frameworks/runtime-src/proj.ios_mac/HelloJavascript.xcodeproj"

xcodebuild -project "$XPROJ" -target HelloJavascript-mobile -configuration Release -sdk iphoneos \
  SYMROOT="$ROOT/build" \
  ARCHS=arm64 VALID_ARCHS=arm64 ONLY_ACTIVE_ARCH=NO IPHONEOS_DEPLOYMENT_TARGET=12.0 \
  ENABLE_BITCODE=NO GCC_TREAT_WARNINGS_AS_ERRORS=NO CLANG_WARN_DOCUMENTATION_COMMENTS=NO \
  OTHER_CFLAGS='$(inherited) -Wno-error -Wno-deprecated-declarations -Wno-implicit-function-declaration' \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY="" DEVELOPMENT_TEAM="" \
  PRODUCT_BUNDLE_IDENTIFIER=com.private.allstarwarrior \
  build > "$ROOT/out/build.log" 2>&1
RC=$?
grep -E "error:|BUILD (SUCCEEDED|FAILED)" "$ROOT/out/build.log" | head -60
tail -5 "$ROOT/out/build.log"
[ $RC -eq 0 ] || exit $RC

APP=$(ls -d "$ROOT"/build/Release-iphoneos/*.app | head -1)
echo "App: $APP"
cd "$ROOT/out"
rm -rf Payload && mkdir Payload
cp -R "$APP" Payload/
zip -qry AllstarShell.ipa Payload
ls -la AllstarShell.ipa
