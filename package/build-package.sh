#!/usr/bin/env bash
# Build and audit the public universal BYO-data package.
set -euo pipefail

export LC_ALL=C
export TZ=UTC

fail() {
  printf 'package error: %s\n' "$*" >&2
  exit 1
}

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
PORT_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd -P)
STATIC_DIR="$SCRIPT_DIR/universal"
R36S_DIR="$SCRIPT_DIR/r36s"
NX_DIR="$PORT_DIR/third_party/NXExtract"
BINARY=${TERRARIA_PACKAGE_BINARY:-"$PORT_DIR/terraria-universal"}
OUTPUT=${1:-"$PORT_DIR/.build/terraria.zip"}
SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH:-1785628800}

if [[ ${TERRARIA_SKIP_BUILD:-0} != 1 ]]; then
  "$PORT_DIR/build_universal.sh"
fi
[[ -x "$BINARY" ]] || fail "universal loader is missing: $BINARY"

for tool in bash cmp file find grep install mktemp python3 readelf \
            sha256sum sort touch unzip zip; do
  command -v "$tool" >/dev/null 2>&1 || fail "missing host tool: $tool"
done

TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/terraria-package.XXXXXX")
STAGE="$TMP_ROOT/stage"
TMP_ZIP="$TMP_ROOT/terraria.zip"
trap 'rm -rf -- "$TMP_ROOT"' EXIT INT TERM
mkdir -p "$STAGE/terraria/gamedata" "$STAGE/terraria/tools" \
  "$STAGE/terraria/licenses"

put() {
  local mode=$1 source=$2 destination=$3
  [[ -f "$source" ]] || fail "missing package source: $source"
  install -D -m "$mode" -- "$source" "$STAGE/$destination"
}

put 0755 "$R36S_DIR/Terraria.sh" "Terraria.sh"
put 0755 "$BINARY" "terraria/terraria"
put 0755 "$PORT_DIR/run.sh" "terraria/run.sh"
put 0755 "$NX_DIR/run-extractor.sh" "terraria/run-extractor.sh"
put 0755 "$NX_DIR/nxextract-runtime-env.sh" "terraria/nxextract-runtime-env.sh"
put 0755 "$NX_DIR/nxextract.py" "terraria/nxextract.py"
put 0755 "$NX_DIR/ui/build/nxextract-ui" "terraria/nxextract-ui"
put 0755 "$PORT_DIR/tools/prepare_terraria_data.py" \
  "terraria/tools/prepare_terraria_data.py"
put 0644 "$STATIC_DIR/extractor.json" "terraria/extractor.json"
put 0644 "$STATIC_DIR/version.txt" "terraria/version.txt"
put 0644 "$STATIC_DIR/gamedata/README.txt" "terraria/gamedata/README.txt"
put 0644 "$STATIC_DIR/README.md" "terraria/README.md"
put 0644 "$STATIC_DIR/INSTALLATION.md" "terraria/INSTALLATION.md"
put 0644 "$PORT_DIR/NOTICE.md" "terraria/NOTICE.md"
put 0644 "$PORT_DIR/CHANGELOG.md" "terraria/CHANGELOG.md"
put 0644 "$PORT_DIR/LICENSE" "terraria/LICENSE"
put 0644 "$R36S_DIR/port.json" "terraria/port.json"
put 0644 "$R36S_DIR/gameinfo.xml" "terraria/gameinfo.xml"
put 0644 "$PORT_DIR/licenses/Apache-2.0.txt" "terraria/licenses/Apache-2.0.txt"
put 0644 "$PORT_DIR/licenses/GPL-3.0.txt" "terraria/licenses/GPL-3.0.txt"
put 0644 "$PORT_DIR/licenses/Producdevity-MIT.txt" "terraria/licenses/Producdevity-MIT.txt"
put 0644 "$PORT_DIR/licenses/Unlicense.txt" "terraria/licenses/Unlicense.txt"
put 0644 "$PORT_DIR/licenses/NXExtract-MIT.txt" "terraria/licenses/NXExtract-MIT.txt"

glibc_at_most() {
  local candidate=$1 maximum=$2 newest version major minor machine
  machine=$(readelf -h "$candidate" |
    sed -n 's/^[[:space:]]*Machine:[[:space:]]*//p')
  [[ $machine == AArch64 ]] ||
    fail "${candidate#"$STAGE/"} is not AArch64 (found: $machine)"
  newest=$(readelf --version-info "$candidate" 2>/dev/null |
    grep -oE 'GLIBC_[0-9]+([.][0-9]+)*' | sort -Vu | tail -1)
  [[ -n $newest ]] || fail "cannot determine glibc ABI: ${candidate#"$STAGE/"}"
  version=${newest#GLIBC_}
  major=${version%%.*}
  minor=${version#*.}; minor=${minor%%.*}
  if (( major > 2 || (major == 2 && minor > maximum) )); then
    fail "${candidate#"$STAGE/"} requires $newest (maximum: GLIBC_2.$maximum)"
  fi
}

# Audit every executable object in the staged release. Exactly two project
# runtime ELFs are permitted; Android owner libraries are never staged.
while IFS= read -r -d '' candidate; do
  kind=$(file -b "$candidate")
  case "$kind" in
    *ELF*)
      relative=${candidate#"$STAGE/"}
      case "$relative" in
        terraria/terraria|terraria/nxextract-ui) ;;
        *) fail "unexpected ELF entered package: $relative" ;;
      esac
      glibc_at_most "$candidate" 30
      ;;
    *PE32*|*Mach-O*)
      fail "foreign executable entered package: ${candidate#"$STAGE/"}"
      ;;
  esac
done < <(find "$STAGE" -type f -print0)

TLS_FILESZ=$(readelf -lW "$STAGE/terraria/terraria" |
  awk '$1 == "TLS" { value=$5 } END { print value }')
PAD_LAYOUT=$(readelf -sW "$STAGE/terraria/terraria" |
  awk '$4 == "TLS" && $8 == "g_bionic_guard_pad" {
    value=$2 ":" $3
  } END { print value }')
[[ $TLS_FILESZ == 0x000100 && $PAD_LAYOUT == 0000000000000000:256 ]] ||
  fail "audited TLS layout changed: template=$TLS_FILESZ pad=$PAD_LAYOUT"

[[ $(tr -d '\r\n' < "$NX_DIR/VERSION") == 1.2.0 ]] ||
  fail "vendored NXExtract is not version 1.2.0"
declare -A NX_HASHES=(
  [nxextract.py]=55664066d2ff0e5b7b83b6285d6606cca74923e80183d2f2e176e6353b93abd5
  [nxextract-runtime-env.sh]=332919a9960d4317563b647f9932d1a4367da147a425fe2f78eafd706f01563f
  [run-extractor.sh]=3c61f638a25f0ca9c5c5a94d33660886aaff17a18347c9e954afd4b0e9b3efba
  [nxextract-ui]=046afb583f5a211c946495e639409f81d9cfec706788eeccb7924b0e8e5a50b6
)
for relative in "${!NX_HASHES[@]}"; do
  actual=$(sha256sum "$STAGE/terraria/$relative" | awk '{print $1}')
  [[ $actual == "${NX_HASHES[$relative]}" ]] ||
    fail "NXExtract runtime hash mismatch: $relative"
done

bash -n "$STAGE/Terraria.sh" "$STAGE/terraria/run-extractor.sh" \
  "$STAGE/terraria/nxextract-runtime-env.sh"
sh -n "$STAGE/terraria/run.sh"
python3 - "$STAGE/terraria/nxextract.py" \
             "$STAGE/terraria/tools/prepare_terraria_data.py" <<'PY'
import sys
for path in sys.argv[1:]:
    with open(path, "rb") as stream:
        compile(stream.read(), path, "exec")
PY
python3 "$STAGE/terraria/nxextract.py" recipe-check \
  --recipe "$STAGE/terraria/extractor.json" >/dev/null

if grep -En '^[[:space:]]*(export[[:space:]]+)?SDL_(VIDEO|AUDIO)DRIVER=' \
    "$STAGE/Terraria.sh" "$STAGE/terraria/run.sh"; then
  fail "launcher must not force an SDL video or audio backend"
fi
if grep -En '(^|[[:space:]])(setsid|nohup|systemctl[[:space:]]+(stop|mask))([[:space:]]|$)' \
    "$STAGE/Terraria.sh" "$STAGE/terraria/run.sh"; then
  fail "launcher contains a forbidden lifecycle command"
fi

python3 - "$STAGE/terraria/port.json" "$STAGE/terraria/gameinfo.xml" <<'PY'
import json
import sys
import xml.etree.ElementTree as ET
with open(sys.argv[1], encoding="utf-8") as stream:
    metadata = json.load(stream)
if metadata.get("version") != 4 or metadata.get("name") != "terraria.zip":
    raise SystemExit("invalid PortMaster metadata identity")
if metadata.get("items") != ["Terraria.sh", "terraria"]:
    raise SystemExit("port.json items do not match archive layout")
if metadata.get("attr", {}).get("arch") != ["aarch64"]:
    raise SystemExit("port.json must declare AArch64")
game = ET.parse(sys.argv[2]).getroot().find("game")
if game is None or game.findtext("path") != "./Terraria.sh":
    raise SystemExit("gameinfo.xml launcher path is invalid")
PY

if find "$STAGE" \( \
    -iname '*.apk' -o -iname '*.apkm' -o -iname '*.apks' -o \
    -iname '*.xapk' -o -iname '*.obb' -o -iname '*.dex' -o \
    -name 'libunity.so' -o -name 'libil2cpp.so' -o \
    -name 'libc++_shared.so' -o -name 'global-metadata.dat' -o \
    -name 'sharedassets*' -o -name '*.unity3d' \
  \) -print -quit | grep -q .; then
  fail "proprietary game data entered the public staging tree"
fi
if find "$STAGE" \( \
    -iname '*.log' -o -iname '*.raw' -o -iname '*.ppm' -o \
    -name 'HANDOFF.md' -o -name '__pycache__' -o -name '*.pyc' -o \
    -name 'userdata' -o -name 'Players' -o -name 'Worlds' \
  \) -print -quit | grep -q .; then
  fail "development or personal artifact entered the public staging tree"
fi
if grep -IRnE '192[.]168[.]|/home/|/mnt/ARQUIVOS|root@' "$STAGE" \
    --include='*.sh' --include='*.py' --include='*.md' \
    --include='*.txt' --include='*.json' --include='*.xml'; then
  fail "release text contains a test address or personal path"
fi

(
  cd "$STAGE"
  find . -type f ! -path './terraria/PACKAGE-MANIFEST.sha256' \
    -printf '%P\n' | sort | while IFS= read -r relative; do
      sha256sum -- "$relative"
    done
) > "$STAGE/terraria/PACKAGE-MANIFEST.sha256"

find "$STAGE" -exec touch -h -d "@$SOURCE_DATE_EPOCH" {} +
(
  cd "$STAGE"
  find . -type f -printf '%P\n' | sort | zip -X -9 -q "$TMP_ZIP" -@
)
unzip -tq "$TMP_ZIP" >/dev/null

VERIFY="$TMP_ROOT/verify"
mkdir -p "$VERIFY"
unzip -q "$TMP_ZIP" -d "$VERIFY"
(
  cd "$VERIFY"
  sha256sum -c terraria/PACKAGE-MANIFEST.sha256 >/dev/null
)

mkdir -p "$(dirname -- "$OUTPUT")"
OUTPUT_DIR=$(cd -- "$(dirname -- "$OUTPUT")" && pwd -P)
OUTPUT="$OUTPUT_DIR/$(basename -- "$OUTPUT")"
install -m 0644 "$TMP_ZIP" "$OUTPUT"
(
  cd "$OUTPUT_DIR"
  sha256sum "$(basename -- "$OUTPUT")" > "$(basename -- "$OUTPUT").sha256"
)

printf 'PACKAGE OK: %s\n' "$OUTPUT"
printf 'loader ABI: GLIBC <= 2.30 | TLS %s %s\n' "$TLS_FILESZ" "$PAD_LAYOUT"
sha256sum "$BINARY" "$OUTPUT"
