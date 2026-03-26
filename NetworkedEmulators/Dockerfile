FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    xvfb ffmpeg x11vnc fluxbox xdotool git \
    build-essential cmake qt5-default libqt5opengl5-dev \
    && rm -rf /var/lib/apt/lists/*

# Build mGBA from source
WORKDIR /opt
RUN git clone https://github.com/mgba-emu/mgba.git
WORKDIR /opt/mgba
RUN mkdir build && cd build && \
    cmake .. -DBUILD_PYTHON=ON -DBUILD_LIBRETRO=OFF && \
    make -j$(nproc) && \
    make install

#optional check
RUN pip install /opt/mgba/build/python

# Python environment
ENV PYTHONPATH="/usr/local/lib/python3.11/site-packages:$PYTHONPATH"
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Saves
RUN mkdir -p /saves

# Display for headless GUI
ENV DISPLAY=:1

# Ports
EXPOSE 8080
ENV ROM_PATH=/roms/pokemon_firered.gba
ENV THEME=firered

# Start Flask app
CMD ["python", "server.py"]