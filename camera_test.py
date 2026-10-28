from pathlib import Path
from datetime import datetime
import os

import requests
import cv2


def send_snapshot(filename):
    print("Entered send_snapshot", flush=True)

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

    if not webhook_url:
        print("Webhook URL is missing. Set it in this terminal.", flush=True)
        return

    try:
        print("Opening saved image...", flush=True)

        with open(filename, "rb") as image:
            print("Starting Discord upload...", flush=True)

            response = requests.post(
                webhook_url,
                params={"wait": "true"},
                data={
                    "content": f"Camera snapshot: {filename.name}"
                },
                files={
                    "files[0]": (filename.name, image, "image/jpeg")
                },
                timeout=(10, 20),
            )

        print(
            f"Discord responded: HTTP {response.status_code}",
            flush=True,
        )

        if response.status_code == 200:
            message = response.json()
            print("Sent to Discord!", flush=True)
            print("Message ID:", message.get("id"), flush=True)
            print("Channel ID:", message.get("channel_id"), flush=True)
        else:
            print("Discord did not confirm the upload.", flush=True)
            print(response.text[:500], flush=True)

    except requests.Timeout:
        print("Upload failed: connection or response timed out.", flush=True)

    except requests.RequestException:
        # Avoid printing an exception that could expose the webhook URL.
        print("Upload failed: network or connection error.", flush=True)

    except OSError:
        print("Upload failed: could not open the saved image.", flush=True)

    except ValueError:
        print("Discord returned an unexpected response.", flush=True)


camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)

output_folder = Path(__file__).resolve().parent / "snapshots"
output_folder.mkdir(exist_ok=True)

try:
    if not camera.isOpened():
        raise RuntimeError(
            "Could not open camera. Try camera number 0, 1, or 2."
        )

    print("Running file:", Path(__file__).resolve(), flush=True)
    print("Click the camera window.", flush=True)
    print("Press S to save and upload. Press Q to quit.", flush=True)

    while True:
        success, frame = camera.read()

        if not success or frame is None:
            raise RuntimeError("Could not read an image from the camera.")

        cv2.imshow("USB Camera - S: snapshot, Q: quit", frame)

        key = cv2.waitKey(1) & 0xFF

        if key in (ord("s"), ord("S")):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = output_folder / f"snapshot_{timestamp}.jpg"

            if not cv2.imwrite(str(filename), frame):
                raise RuntimeError(f"Could not save {filename}")

            print(f"Saved: {filename}", flush=True)
            send_snapshot(filename)

        elif key in (ord("q"), ord("Q")):
            break

except KeyboardInterrupt:
    print("\nStopped.", flush=True)

finally:
    camera.release()
    cv2.destroyAllWindows()