#!/usr/bin/env bash
set -euo pipefail

# Always work from this script's folder.
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [[ ! -f camera_app.py ]]; then
    echo "Cannot find camera_app.py beside this launcher."
    read -r -p "Press Enter to close."
    exit 1
fi

# Install dependencies only if the imports fail.
if ! /usr/bin/python3 -c \
    "import tkinter, cv2, requests; from PIL import Image, ImageTk" \
    >/dev/null 2>&1; then

    echo "Installing Vigil dependencies. Internet is required."
    sudo apt-get update
    sudo apt-get install -y \
        python3-tk \
        python3-opencv \
        python3-requests \
        python3-pil \
        python3-pil.imagetk
fi

echo "Starting Vigil..."
/usr/bin/python3 "$PROJECT_DIR/camera_app.py"