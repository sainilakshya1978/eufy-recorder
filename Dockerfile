FROM bropat/eufy-security-ws:latest

# 1. Install Python, FFmpeg & Tools
RUN apk add --no-cache python3 py3-pip ffmpeg netcat-openbsd curl
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install pyTelegramBotAPI websocket-client flask requests pytz

# 2. Copy Main Script
COPY main.py /main.py

# 3. Ultimate Robust Startup Script
# - Config create karega
# - Node Driver start karega
# - Python tabhi chalega jab Port 3000 open ho jayega
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'mkdir -p /usr/src/app' >> /start.sh && \
    echo 'echo "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\",\"country\":\"IN\",\"trustedDeviceName\":\"Koyeb_Ultimate\"}" > /usr/src/app/config.json' >> /start.sh && \
    echo 'echo "🚀 Starting Eufy Driver..."' >> /start.sh && \
    echo 'node dist/bin/server.js &' >> /start.sh && \
    echo 'echo "⏳ Waiting for Port 3000 to open..."' >> /start.sh && \
    echo 'while ! nc -z 127.0.0.1 3000; do sleep 1; done' >> /start.sh && \
    echo 'echo "✅ Port 3000 is Open! Starting Bot..."' >> /start.sh && \
    echo 'python3 /main.py' >> /start.sh

RUN chmod +x /start.sh
ENTRYPOINT []
CMD ["/start.sh"]
