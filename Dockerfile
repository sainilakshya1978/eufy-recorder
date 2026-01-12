FROM bropat/eufy-security-ws:latest

# 1. Install Tools
RUN apk add --no-cache python3 py3-pip ffmpeg

# 2. Virtual Env
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Install Libs
RUN pip install pyTelegramBotAPI websocket-client flask

# 4. Copy Main Script
COPY main.py /main.py

# 5. Create Config Generator Script (Python se banayenge taaki syntax error na ho)
RUN echo 'import os, json' > /gen_config.py && \
    echo 'config = {' >> /gen_config.py && \
    echo '  "username": os.environ.get("USERNAME"),' >> /gen_config.py && \
    echo '  "password": os.environ.get("PASSWORD"),' >> /gen_config.py && \
    echo '  "country": "IN",' >> /gen_config.py && \
    echo '  "language": "en",' >> /gen_config.py && \
    echo '  "trustedDeviceName": "KoyebBot",' >> /gen_config.py && \
    echo '  "acceptInvitations": True' >> /gen_config.py && \
    echo '}' >> /gen_config.py && \
    echo 'print("Generating config for:", config["username"])' >> /gen_config.py && \
    echo 'with open("/usr/src/app/config.json", "w") as f:' >> /gen_config.py && \
    echo '  json.dump(config, f)' >> /gen_config.py

# 6. Startup Script
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'echo "-----------------------------------"' >> /start.sh && \
    echo 'python3 /gen_config.py' >> /start.sh && \
    echo 'echo "Config created. Starting Driver..."' >> /start.sh && \
    echo 'echo "-----------------------------------"' >> /start.sh && \
    echo 'node dist/bin/server.js &' >> /start.sh && \
    echo 'echo "Waiting 20s for driver..."' >> /start.sh && \
    echo 'sleep 20' >> /start.sh && \
    echo 'echo "Starting Python Bot..."' >> /start.sh && \
    echo 'python3 /main.py' >> /start.sh

RUN chmod +x /start.sh

# 7. Expose & Run
EXPOSE 5000 8000
ENTRYPOINT []
CMD ["/start.sh"]
