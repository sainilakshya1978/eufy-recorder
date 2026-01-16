FROM bropat/eufy-security-ws:latest

# Dependencies
RUN apk add --no-cache python3 py3-pip ffmpeg netcat-openbsd
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install pyTelegramBotAPI websocket-client flask requests pytz

COPY main.py /main.py

# ULTIMATE STARTUP LOGIC
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'mkdir -p /usr/src/app' >> /start.sh && \
    echo 'echo "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\",\"country\":\"IN\",\"trustedDeviceName\":\"Koyeb_Final\"}" > /usr/src/app/config.json' >> /start.sh && \
    echo 'node dist/bin/server.js &' >> /start.sh && \
    echo 'echo "⏳ Waiting for Eufy Driver on Port 3000..."' >> /start.sh && \
    echo 'while ! nc -z localhost 3000; do sleep 2; done' >> /start.sh && \
    echo 'echo "✅ Driver is UP! Launching Python Bot..."' >> /start.sh && \
    echo 'python3 /main.py' >> /start.sh

RUN chmod +x /start.sh
ENTRYPOINT []
CMD ["/start.sh"]
