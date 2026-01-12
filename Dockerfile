FROM bropat/eufy-security-ws:latest

# 1. Install dependencies
RUN apk add --no-cache python3 py3-pip ffmpeg

# 2. Virtual Env
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Python Libs
RUN pip install pyTelegramBotAPI websocket-client flask

# 4. Copy Code
COPY main.py /main.py

# 5. Generate Config (Iphone Trick)
#    Hum device ka naam "MyiPhone" rakh rahe hain taaki Captcha na mangey
RUN echo 'import os, json' > /gen_config.py && \
    echo 'config = {' >> /gen_config.py && \
    echo '  "username": os.environ.get("USERNAME"),' >> /gen_config.py && \
    echo '  "password": os.environ.get("PASSWORD"),' >> /gen_config.py && \
    echo '  "country": "IN",' >> /gen_config.py && \
    echo '  "language": "en",' >> /gen_config.py && \
    echo '  "trustedDeviceName": "MyiPhone13",' >> /gen_config.py && \
    echo '  "acceptInvitations": True' >> /gen_config.py && \
    echo '}' >> /gen_config.py && \
    echo 'with open("/usr/src/app/config.json", "w") as f:' >> /gen_config.py && \
    echo '  json.dump(config, f, indent=2)' >> /gen_config.py

# 6. Startup Script
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'echo "--- SYSTEM STARTING ---"' >> /start.sh && \
    echo 'python3 /gen_config.py' >> /start.sh && \
    echo 'echo "Config Generated. Starting Driver..."' >> /start.sh && \
    echo 'node dist/bin/server.js &' >> /start.sh && \
    echo 'echo "Waiting 30s for Driver Login..."' >> /start.sh && \
    echo 'sleep 30' >> /start.sh && \
    echo 'echo "Starting Python Logic..."' >> /start.sh && \
    echo 'python3 /main.py' >> /start.sh

RUN chmod +x /start.sh

EXPOSE 5000 8000
ENTRYPOINT []
CMD ["/start.sh"]
