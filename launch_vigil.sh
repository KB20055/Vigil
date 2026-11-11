#!/usr/bin/env bash
set -euo pipefail

# Always work from this script's folder.
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

VENV_DIR="$PROJECT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

if [[ ! -f camera_app.py ]]; then
    echo "Cannot find camera_app.py beside this launcher."
    read -r -p "Press Enter to close."
    exit 1
fi

# Install system dependencies if needed.
if ! /usr/bin/python3 -c \
    "import tkinter, cv2, requests; from PIL import Image, ImageTk" \
    >/dev/null 2>&1; then

    echo "Installing Vigil system dependencies..."
    sudo apt-get update
    sudo apt-get install -y \
        python3-tk \
        python3-opencv \
        python3-requests \
        python3-pil \
        python3-pil.imagetk \
        python3-venv
fi

# Ensure Python virtual environment support is installed.
if ! /usr/bin/python3 -c "import venv" >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y python3-venv
fi

# Create virtual environment if it doesn't exist.
if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "Creating Vigil Python environment..."
    /usr/bin/python3 -m venv --system-site-packages "$VENV_DIR"
fi

# Install Ultralytics and its dependencies if missing.
if ! "$VENV_PYTHON" -c "from ultralytics import YOLO" \
    >/dev/null 2>&1; then

    echo "Installing Ultralytics YOLO dependencies..."
    "$VENV_PYTHON" -m pip install ultralytics
fi

# Verify all required dependencies.
echo "Checking Vigil dependencies..."

"$VENV_PYTHON" -c \
    "import tkinter, cv2, requests; from PIL import Image, ImageTk; from ultralytics import YOLO"

echo "All dependencies installed successfully!"
echo "Starting Vigil..."

# Launch Vigil using the virtual environment.
exec "$VENV_PYTHON" "$PROJECT_DIR/camera_app.py"