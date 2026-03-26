FROM python:3.11-slim

# System dependencies for GUI + headless display
WORKDIR /opt/mgba

RUN apt-get update --allow-releaseinfo-change && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        xvfb \
        ffmpeg \
        x11vnc \
        fluxbox \
        xdotool \
        git \
        build-essential \
        python3-dev \
        swig \
        libgl1 \
        libglu1-mesa \
        libglib2.0-0 \
        libpng-dev \
        zlib1g-dev \
        curl \
        xz-utils \
    && curl -L -o mgba.tar.xz https://github.com/mgba-emu/mgba/releases/download/0.10.5/mGBA-0.10.5-ubuntu64-jammy.tar.xz \
    && tar xf mgba.tar.xz --strip-components=1 \
    && ln -s /opt/mgba/mgba /usr/local/bin/mgba \
    && rm mgba.tar.xz \
    && rm -rf /var/lib/apt/lists/*

#app configs
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /saves

# Headless GUI setup + debug startup
ENV DISPLAY=:1
RUN echo '#!/bin/bash\n\
echo "Starting container with THEME=$THEME and ROM_PATH=$ROM_PATH"\n\
Xvfb :1 -screen 0 1024x768x16 &\n\
exec "$@"' > /entrypoint.sh && chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# Ports
EXPOSE 8080 6000

# Environment variables (default fallback)
ENV PYTHONPATH="/usr/local/lib/python3.11/site-packages:$PYTHONPATH"
ENV THEME=firered
ENV ROM_PATH=/roms/pokemon_firered.gba

# Start Flask app
CMD ["python", "server.py"]
