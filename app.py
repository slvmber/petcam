from flask import Flask, render_template, abort, request, Response
import cv2
import threading
import time

app = Flask(__name__)

camera = None
camera_lock = threading.Lock()


def get_camera():
    global camera

    with camera_lock:
        if camera is None or not camera.isOpened():
            print("Opening camera...")

            camera = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)

            if not camera.isOpened():
                print("ERROR: Could not open /dev/video0")
                camera = None
                return None

            # Optional: set resolution
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            print("Camera opened successfully")

        return camera


def reset_camera():
    global camera

    with camera_lock:
        if camera is not None:
            print("Releasing camera...")
            camera.release()
            camera = None


def generate_frames():
    while True:

        cam = get_camera()

        if cam is None:
            print("Camera unavailable, retrying...")
            time.sleep(2)
            continue

        # Only one thread can access VideoCapture at a time
        with camera_lock:
            success, frame = cam.read()

        if not success:
            print("Camera frame failed, reconnecting...")

            reset_camera()

            time.sleep(1)
            continue

        success, buffer = cv2.imencode(".jpg", frame)

        if not success:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/debug")
def debug():
    user_ip = request.remote_addr

    if not (
        user_ip.startswith("192.168.1.")
        or user_ip == "127.0.0.1"
    ):
        abort(403)

    return "<h1>PetCam Debug Panel</h1><p>Access granted.</p>"


@app.errorhandler(403)
def forbidden(error):
    return render_template("403.html"), 403


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )
