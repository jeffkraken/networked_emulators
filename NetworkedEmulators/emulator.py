import os
import threading
import subprocess
import time
import socket
import numpy as np
import cv2

class Emulator:
    def __init__(self, rom_path=None):
        self.rom_path = rom_path or os.getenv("ROM_PATH")
        if not self.rom_path:
            raise RuntimeError("ROM_PATH environment variable must be set")

        print(f"Loading ROM: {self.rom_path}")

        self.running = False
        self.latest_frame = None
        self.lock = threading.Lock()
        self.process = None

        # Multiplayer configuration
        self.link_mode = os.getenv("LINK_MODE", "none")  # host / client / none
        self.link_port = int(os.getenv("LINK_PORT", 6000))
        self.link_host = os.getenv("LINK_HOST", "localhost")
        self.sync_port = int(os.getenv("SYNC_PORT", 7000))
        self.is_host = self.link_mode == "host"

        # Python GBA bindings (optional)
        self.pygba = None

    def start(self):
        """Launch mGBA headless with Xvfb and start frame capture + multiplayer threads."""
        self.running = True

        # Build mGBA command
        cmd = ["mgba", "-g", self.rom_path]

        if self.link_mode == "host":
            cmd += ["--multiplayer", f"--link=:{self.link_port}"]
        elif self.link_mode == "client":
            cmd += ["--multiplayer", f"--link={self.link_host}:{self.link_port}"]

        # Use xvfb-run to automatically pick a display
        cmd = ["xvfb-run", "-a", "-s", "-screen 0 240x160x24"] + cmd

        print("Launching mGBA:", " ".join(cmd))
        self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Start threads for frame capture and multiplayer sync
        threading.Thread(target=self.capture_loop, daemon=True).start()
        threading.Thread(target=self.frame_sync_loop, daemon=True).start()

    def capture_loop(self):
        """Capture emulator frames from Xvfb via ffmpeg."""
        ffmpeg_cmd = [
            "ffmpeg",
            "-f", "x11grab",
            "-video_size", "240x160",
            "-i", os.getenv("DISPLAY", ":99"),  # will match xvfb-run assigned display
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-"
        ]
        try:
            pipe = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, bufsize=10**8)
        except Exception as e:
            print(f"Error starting ffmpeg: {e}")
            return

        frame_size = 240 * 160 * 3
        while self.running:
            raw = pipe.stdout.read(frame_size)
            if len(raw) != frame_size:
                time.sleep(0.001)
                continue
            frame = np.frombuffer(raw, dtype=np.uint8).reshape((160, 240, 3))
            with self.lock:
                self.latest_frame = frame

    def frame_sync_loop(self):
        """Host/client tick synchronization for multiplayer."""
        if self.is_host:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("0.0.0.0", self.sync_port))
            server.listen(1)
            print(f"Sync host listening on port {self.sync_port}")
            conn, addr = server.accept()
            print(f"Sync client connected from {addr}")

            while self.running:
                if self.pygba:
                    self.pygba.tick()
                try:
                    conn.sendall(b"tick")
                except Exception:
                    break
                time.sleep(1 / 60)
        elif self.link_mode == "client":
            time.sleep(2)
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((self.link_host, self.sync_port))
            print(f"Connected to sync host {self.link_host}:{self.sync_port}")

            while self.running:
                data = client.recv(4)
                if data == b"tick" and self.pygba:
                    self.pygba.tick()
                else:
                    time.sleep(0.001)

    def get_frame(self):
        with self.lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def handle_input(self, action, event_type="down"):
        if not self.pygba:
            print("Warning: Python GBA bindings not initialized; input disabled")
            return
        pressed = event_type == "down"
        self.pygba.set_button(1, action.upper(), pressed)

    def release_all(self):
        if not self.pygba:
            return
        for btn in ["A","B","L","R","UP","DOWN","LEFT","RIGHT","START","SELECT"]:
            self.pygba.set_button(1, btn, False)

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()