FROM bropat/eufy-security-ws:latest

# 1. Install Python & Tools
RUN apk add --no-cache python3 py3-pip ffmpeg

# 2. Virtual Env Setup
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Install Libraries
RUN pip install pyTelegramBotAPI websocket-client flask

# 4. Copy Python Script
COPY main.py /main.py

# 5. Startup Script (Fix for Config & Logs)
#    Hum config file banayenge aur Node.js ko 'foreground' log mode mein chalayenge
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'echo "-----------------------------------"' >> /start.sh && \
    echo 'echo "Generating Config File..."' >> /start.sh && \
    echo 'echo "{' >> /start.sh && \
    echo '  \"username\": \"$USERNAME\",' >> /start.sh && \
    echo '  \"password\": \"$PASSWORD\",' >> /start.sh && \
    echo '  \"country\": \"IN\",' >> /start.sh && \
    echo '  \"language\": \"en\",' >> /start.sh && \
    echo '  \"trustedDeviceName\": \"KoyebBot\",' >> /start.sh && \
    echo '  \"acceptInvitations\": true' >> /start.sh && \
    echo '}" > /usr/src/app/config.json' >> /start.sh && \
    echo 'echo "-----------------------------------"' >> /start.sh && \
    echo 'echo "STARTING EUFY DRIVER (Watch logs carefully)..."' >> /start.sh && \
    echo 'node dist/bin/server.js &' >> /start.sh && \
    echo 'echo "Waiting 20s for driver initialization..."' >> /start.sh && \
    echo 'sleep 20' >> /start.sh && \
    echo 'echo "Starting Python Bot..."' >> /start.sh && \
    echo 'python3 /main.py' >> /start.sh

RUN chmod +x /start.sh

# 6. Expose Ports
EXPOSE 5000 8000

# 7. Start
ENTRYPOINT []
CMD ["/start.sh"]
