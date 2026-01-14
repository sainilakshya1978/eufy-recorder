FROM bropat/eufy-security-ws:latest

# 1. Install Dependencies
RUN apk add --no-cache python3 py3-pip ffmpeg
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install pyTelegramBotAPI websocket-client flask requests pytz

# 2. Copy Script
COPY main.py /main.py

# 3. Dynamic Config Generator (Safe for Special Characters)
RUN echo 'import os, json' > /gen_config.py && \
    echo 'config = {' >> /gen_config.py && \
    echo '  "username": os.environ.get("USERNAME"),' >> /gen_config.py && \
    echo '  "password": os.environ.get("PASSWORD"),' >> /gen_config.py && \
    echo '  "country": "IN",' >> /gen_config.py && \
    echo '  "trustedDeviceName": os.environ.get("TRUSTED_DEVICE_NAME", "Koyeb_Cloud_Bot"),' >> /gen_config.py && \
    echo '  "acceptInvitations": True' >> /gen_config.py && \
    echo '}' >> /gen_config.py && \
    echo 'with open("/usr/src/app/config.json", "w") as f:' >> /gen_config.py && \
    echo '  json.dump(config, f, indent=2)' >> /gen_config.py

# 4. Advanced Startup Script
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'python3 /gen_config.py' >> /start.sh && \
    echo 'echo "🚀 Starting Eufy Driver..."' >> /start.sh && \
    echo 'node dist/bin/server.js &' >> /start.sh && \
    echo 'echo "⏳ Waiting 40s for Cloud Handshake..."' >> /start.sh && \
    echo 'sleep 40' >> /start.sh && \
    echo 'echo "🤖 Starting Telegram Bot..."' >> /start.sh && \
    echo 'python3 /main.py' >> /start.sh

RUN chmod +x /start.sh
EXPOSE 5000 3000
ENTRYPOINT []
CMD ["/start.sh"]
