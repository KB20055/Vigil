from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
from threading import Thread
from urllib.parse import urlparse
import os
import tkinter as tk
from tkinter import ttk, messagebox

import cv2
import requests
from PIL import Image, ImageTk


class CameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vigil Camera")
        self.root.geometry("920x720")

        self.camera = None
        self.frame = None
        self.uploading = False
        self.events = Queue()

        self.output_folder = (
            Path.home() / "Documents" / "Vigil" / "snapshots"
        )
        self.output_folder.mkdir(parents=True, exist_ok=True)

        self.camera_number = tk.StringVar(value="1")
        self.webhook = tk.StringVar(
            value=os.environ.get("DISCORD_WEBHOOK_URL", "")
        )
        self.status = tk.StringVar(value="Ready. Start the camera.")

        controls = ttk.Frame(root, padding=10)
        controls.pack(fill="x")

        ttk.Label(controls, text="Camera number:").pack(side="left")

        ttk.Spinbox(
            controls,
            from_=0,
            to=10,
            textvariable=self.camera_number,
            width=4,
        ).pack(side="left", padx=8)

        ttk.Button(
            controls, text="Start Camera", command=self.start_camera
        ).pack(side="left", padx=4)

        ttk.Button(
            controls, text="Stop Camera", command=self.stop_camera
        ).pack(side="left", padx=4)

        settings = ttk.Frame(root, padding=(10, 0, 10, 10))
        settings.pack(fill="x")

        ttk.Label(settings, text="Discord webhook:").pack(side="left")

        ttk.Entry(
            settings, textvariable=self.webhook, show="*"
        ).pack(side="left", fill="x", expand=True, padx=8)

        self.preview = tk.Label(
            root,
            text="Camera preview",
            bg="#202020",
            fg="white",
        )
        self.preview.pack(fill="both", expand=True, padx=10)

        self.capture_button = ttk.Button(
            root,
            text="Capture & Send",
            command=self.capture,
            state="disabled",
        )
        self.capture_button.pack(pady=10)

        ttk.Label(
            root,
            textvariable=self.status,
            wraplength=880,
            padding=10,
        ).pack(fill="x")

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(30, self.update_preview)
        self.root.after(100, self.check_events)

    def start_camera(self):
        if self.camera is not None:
            return

        try:
            index = int(self.camera_number.get())
        except ValueError:
            messagebox.showerror("Camera", "Enter a camera number.")
            return

        self.status.set("Opening camera...")
        self.root.update_idletasks()

        if os.name == "nt":
            camera = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        else:
            camera = cv2.VideoCapture(index)

        if not camera.isOpened():
            camera.release()
            self.status.set(
                "Could not open camera. Try 0, 1, or 2, "
                "and close other camera applications."
            )
            return

        self.camera = camera
        self.status.set(f"Camera {index} started.")

    def stop_camera(self):
        if self.camera is not None:
            self.camera.release()
            self.camera = None

        self.frame = None
        self.preview.configure(image="", text="Camera stopped")
        self.preview.image = None
        self.capture_button.configure(state="disabled")
        self.status.set("Camera stopped.")

    def update_preview(self):
        if self.camera is not None:
            success, frame = self.camera.read()

            if success and frame is not None:
                self.frame = frame
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(rgb)

                # Resize the preview only; save the original frame.
                image.thumbnail((880, 500))
                photo = ImageTk.PhotoImage(image)

                self.preview.configure(image=photo, text="")
                self.preview.image = photo

                if not self.uploading:
                    self.capture_button.configure(state="normal")
            else:
                self.stop_camera()
                self.status.set(
                    "Camera frame failed. Check the connection, then restart."
                )

        self.root.after(30, self.update_preview)

    def capture(self):
        if self.frame is None or self.uploading:
            return

        url = self.webhook.get().strip()
        parsed = urlparse(url)

        if (
            parsed.scheme != "https"
            or parsed.hostname != "discord.com"
            or not parsed.path.startswith("/api/webhooks/")
        ):
            messagebox.showerror(
                "Webhook",
                "Paste a Discord webhook URL beginning with "
                "https://discord.com/api/webhooks/",
            )
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = self.output_folder / f"snapshot_{timestamp}.jpg"

        try:
            saved = cv2.imwrite(str(filename), self.frame.copy())
            if not saved:
                raise OSError("Image could not be saved.")
        except (OSError, cv2.error):
            self.status.set("Could not save the snapshot.")
            return

        self.uploading = True
        self.capture_button.configure(state="disabled")
        self.status.set(f"Saved {filename.name}. Uploading...")

        Thread(
            target=self.upload,
            args=(filename, url),
            daemon=True,
        ).start()

    def upload(self, filename, url):
        # Worker threads report through a queue; only the main
        # thread updates Tkinter widgets.
        try:
            with filename.open("rb") as image:
                response = requests.post(
                    url,
                    params={"wait": "true"},
                    data={
                        "content": f"Camera snapshot: {filename.name}"
                    },
                    files={
                        "files[0]": (
                            filename.name,
                            image,
                            "image/jpeg",
                        )
                    },
                    timeout=(10, 20),
                )

            if response.status_code == 200:
                result = "Snapshot sent to Discord."
            elif response.status_code == 429:
                result = "Discord rate limit reached. Wait before retrying."
            else:
                result = (
                    f"Upload failed: HTTP {response.status_code}. "
                    "Snapshot remains saved locally."
                )

        except requests.Timeout:
            result = (
                "Upload timed out; delivery is unconfirmed. "
                "Check Discord before retrying."
            )
        except requests.RequestException:
            result = "Network error. Snapshot remains saved locally."
        except OSError:
            result = "Could not open the saved snapshot."

        self.events.put(result)

    def check_events(self):
        try:
            while True:
                result = self.events.get_nowait()
                self.uploading = False
                self.status.set(result)
        except Empty:
            pass

        self.root.after(100, self.check_events)

    def close(self):
        if self.uploading:
            leave = messagebox.askyesno(
                "Upload in progress",
                "An upload is still running. Exit anyway? "
                "Delivery may be interrupted.",
            )
            if not leave:
                return

        if self.camera is not None:
            self.camera.release()

        self.root.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    app = CameraApp(window)
    window.mainloop()