#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

DESKTOP_DIR="$(xdg-user-dir DESKTOP)"
LAUNCHER="$DESKTOP_DIR/Vigil.desktop"

mkdir -p "$DESKTOP_DIR"

cat > "$LAUNCHER" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Vigil Camera
Comment=Start the Vigil camera application
Exec=bash "$PROJECT_DIR/launch_vigil.sh"
Path=$PROJECT_DIR
Icon=camera-photo
Terminal=true
Categories=AudioVideo;
EOF

chmod +x "$LAUNCHER"
echo "Created desktop launcher: $LAUNCHER"