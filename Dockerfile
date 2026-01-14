FROM bropat/eufy-security-ws:latest

# 1. Sabhi zaroori tools install karein
RUN apk add --no-cache python3 py3-pip ffmpeg
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install pyTelegramBotAPI websocket-client flask requests pytz

# 2. Main script copy karein
COPY main.py /main.py

# 3. Robust Startup: Config file ko runtime pe create karna
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'mkdir -p /usr/src/app' >> /start.sh && \
    echo 'echo "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\",\"country\":\"IN\",\"trustedDeviceName\":\"Koyeb_Pro_Bot\"}" > /usr/src/app/config.json' >> /start.sh && \
    echo 'node dist/bin/server.js &' >> /start.sh && \
    echo 'echo "⏳ Waiting for Eufy Driver to stabilize..." && sleep 35' >> /start.sh && \
    echo 'python3 /main.py' >> /start.sh

RUN chmod +x /start.sh
ENTRYPOINT []
CMD ["/start.sh"]
