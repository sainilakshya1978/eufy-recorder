FROM bropat/eufy-security-ws:latest

RUN apk add --no-cache python3 py3-pip ffmpeg
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install pyTelegramBotAPI websocket-client flask requests pytz

COPY main.py /main.py

# Start script
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'node dist/bin/server.js &' >> /start.sh && \
    echo 'sleep 20' >> /start.sh && \
    echo 'python3 /main.py' >> /start.sh

RUN chmod +x /start.sh
ENTRYPOINT []
CMD ["/start.sh"]
