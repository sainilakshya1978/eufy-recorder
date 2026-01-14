FROM bropat/eufy-security-ws:latest

# Dependencies
RUN apk add --no-cache python3 py3-pip ffmpeg
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install pyTelegramBotAPI websocket-client flask requests pytz

COPY main.py /main.py

# Startup logic with AUTO-CONFIG Generation
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'echo "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\",\"country\":\"IN\",\"trustedDeviceName\":\"Koyeb_Bot\"}" > /usr/src/app/config.json' >> /start.sh && \
    echo 'node dist/bin/server.js &' >> /start.sh && \
    echo 'sleep 25' >> /start.sh && \
    echo 'python3 /main.py' >> /start.sh

RUN chmod +x /start.sh
ENTRYPOINT []
CMD ["/start.sh"]
