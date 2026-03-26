from flask import Flask, render_template, request
from flask_socketio import SocketIO
from emulator import Emulator
import base64
import cv2
import time
import os
import signal
import sys

# initialize flask app
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# load rom path from environment
ROM_PATH = os.getenv("ROM_PATH")
if not ROM_PATH:
    raise RuntimeError("rom_path environment variable must be set to either firered or leafgreen")
print(f"loading rom: {ROM_PATH}")

# load theme from environment for front-end styling
THEME = os.getenv("THEME", "firered")
print(f"using theme: {THEME}")

# instantiate emulator
emulator = Emulator(ROM_PATH)

# start emulator in background thread
socketio.start_background_task(emulator.start)

# define default key mapping from keyboard to gba buttons
key_mapping = {
    "arrowup": "UP",
    "arrowdown": "DOWN",
    "arrowleft": "LEFT",
    "arrowright": "RIGHT",
    "z": "A",
    "x": "B",
    "enter": "START",
    "shift": "SELECT",
    "q": "L",
    "w": "R"
}

# stream frames to clients at approximately 30 fps
def stream_frames():
    while True:
        frame = emulator.get_frame()
        if frame is not None:
            _, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            socketio.emit(
                "frame",
                base64.b64encode(buffer).decode("utf-8")
            )
        time.sleep(1/30)

# serve main page
@app.route("/")
def index():
    # pass theme to html for styling
    return render_template("index.html", theme=THEME)

# handle key press events from client
@socketio.on("key_event")
def key_event(data):
    key = data["key"].lower()
    event_type = data["type"]
    action = key_mapping.get(key)
    if action:
        emulator.handle_input(action, event_type)

# release all pressed buttons
@socketio.on("release_all")
def release_all():
    emulator.release_all()

# client connection events
@socketio.on("connect")
def on_connect():
    print("client connected")

@socketio.on("disconnect")
def on_disconnect():
    print("client disconnected")

# handle container shutdown and clean up emulator
def cleanup(*args):
    print("stopping emulator")
    emulator.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# start background streaming and flask server
if __name__ == "__main__":
    socketio.start_background_task(stream_frames)
    socketio.run(app, host="0.0.0.0", port=8080, allow_unsafe_werkzeug=True)
