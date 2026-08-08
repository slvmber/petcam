from flask import Flask, render_template, abort, request, Response
import cv2

app = Flask(__name__)

# Open the first webcam
camera = None

def get_camera():
    global camera

    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture("/dev/video0")

    return camera

def generate_frames():
    while True:
        cam = get_camera()

        success, frame = cam.read()

        if not success:
            print("Camera frame failed, reconnecting...")
            cam.release()
            continue

        success, buffer = cv2.imencode(".jpg", frame)

        if not success:
            continue

        frame = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame
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

    # Allow local testing from the VM and your LAN
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
    app.run(host="0.0.0.0", port=5000)
