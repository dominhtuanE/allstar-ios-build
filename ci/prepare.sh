#!/bin/bash
# Tai engine-native (Cocos Creator 2.4.2) + thu vien external, dung du an iOS tu template js-template-link.
set -euo pipefail
ROOT="$(pwd)"
ENGINE="$ROOT/engine"
PROJ="$ROOT/proj"

git clone --depth 1 --branch "$ENGINE_TAG" https://github.com/cocos/engine-native.git "$ENGINE"

curl -sSL -o /tmp/external.zip "https://github.com/cocos-creator/cocos2d-x-lite-external/archive/refs/tags/$EXTERNAL_TAG.zip"
unzip -q /tmp/external.zip -d /tmp/ext
EXT_DIR=$(ls -d /tmp/ext/*/ | head -1)
mkdir -p "$ENGINE/external"
cp -R "$EXT_DIR". "$ENGINE/external/"
ls "$ENGINE/external" | head -30

# template tro tuyet doi toi /Applications/CocosCreator.app/Contents/Resources/cocos2d-x -> lien ket toi engine
sudo mkdir -p /Applications/CocosCreator.app/Contents/Resources
sudo ln -sfn "$ENGINE" /Applications/CocosCreator.app/Contents/Resources/cocos2d-x

# libjs_static.a (spidermonkey cu) khong con tren iOS (dung JavaScriptCore) -> tao thu vien rong neu thieu
LJS="$ENGINE/external/ios/libs/libjs_static.a"
if [ ! -f "$LJS" ]; then
  mkdir -p "$(dirname "$LJS")"
  echo 'void pv_empty_symbol(void){}' > /tmp/empty.c
  xcrun -sdk iphoneos clang -c /tmp/empty.c -o /tmp/empty.o -arch arm64 -miphoneos-version-min=12.0
  xcrun ar rcs "$LJS" /tmp/empty.o
fi

# du an: copy template + tai nguyen gia (du lieu that ghep sau tren Windows)
mkdir -p "$PROJ"
cp -R "$ENGINE/templates/js-template-link/." "$PROJ/"
mkdir -p "$PROJ/jsb-adapter" "$PROJ/assets" "$PROJ/src"
echo "placeholder" > "$PROJ/jsb-adapter/README.txt"
echo "placeholder" > "$PROJ/assets/README.txt"
[ -f "$PROJ/project.json" ] || echo '{}' > "$PROJ/project.json"

python3 ci/patch.py "$ENGINE" "$PROJ"
