## Project

Dockerized mGBA-based GBA emulator with multiplayer support, headless Xvfb display, and Flask web interface.

## Current Status

- Dockerfile builds successfully, installs mGBA from official GitHub releases, sets up headless display and dependencies.
- Flask server runs inside containers exposing ports 8080/8081 with two emulator instances (FireRed and LeafGreen).
- Emulator subprocess fails to launch mgba due to FileNotFoundError (executable not found in PATH).
- Symlink /usr/local/bin/mgba exists in image but likely not accessible or PATH misconfigured.
- Video frames show black screens because emulator process isn’t running.
- Need to fix subprocess launch by using absolute path to mGBA binary and confirm container PATH and symlink.
- Also verifying ffmpeg capturing Xvfb frames and multiplayer socket sync code.

## Next steps

- Check existence and permissions of /usr/local/bin/mgba inside the container.
- Modify emulator.py to launch mGBA with absolute path "/usr/local/bin/mgba".
- Confirm environment PATH includes /usr/local/bin.
- Test running mGBA manually inside container shell.
- Verify ffmpeg command grabs frames correctly from Xvfb.
- Resume troubleshooting black frames and multiplayer sync.

## HEADS UP
After cloning:
- cd {repo}/networked_emulators && mkdir saves roms
- Then download legally obtained roms for fire red and leaf green, be sure to save as pokemon_firered.gba and pokemon_leafgreen.gba in the roms directory
