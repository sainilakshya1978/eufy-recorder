FROM bropat/eufy-security-ws:latest

# Core dependencies for No-Refusal Logic & FFmpeg
RUN apk add --no-cache python3 py3-pip ffmpeg netcat-openbsd curl
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the strict requirements and install
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY main.py /main.py

# ULTIMATE STARTUP LOGIC: IPv4 Bridge (HOST=0.0.0.0) & Parallel Launch
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'mkdir -p /usr/src/app' >> /start.sh && \
    echo 'echo "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\",\"country\":\"IN\",\"trustedDeviceName\":\"Koyeb_Titanium\"}" > /usr/src/app/config.json' >> /start.sh && \
    echo 'HOST=0.0.0.0 node dist/bin/server.js & ' >> /start.sh && \
    echo 'python3 /main.py' >> /start.sh

RUN chmod +x /start.sh
ENTRYPOINT []
CMD ["/start.sh"]
