#!/usr/bin/env bash
# Source-tree convenience launcher. The packaged PortMaster entry point lives
# under package/r36s and receives this directory explicitly.
set -e
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" 2>/dev/null && pwd -P) || exit 1
export TERRARIA_GAME_DIR="$SCRIPT_DIR"
exec "$SCRIPT_DIR/package/r36s/Terraria.sh" "$@"
