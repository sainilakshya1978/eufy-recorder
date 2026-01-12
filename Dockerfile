FROM bropat/eufy-security-ws:latest

# 1. Install Python, pip, ffmpeg
RUN apk add --no-cache python3 py3-pip ffmpeg

# 2. Setup Virtual Environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Install Python Libraries
RUN pip install pyTelegramBotAPI websocket-client flask

# 4. Copy Main Script
COPY main.py /main.py

# 5. Create Config Generator (Python Script to avoid JSON Syntax Errors)
#    Yeh script environment variables se clean config.json banayegi
RUN echo 'import os, json' > /gen_config.py && \
    echo 'config = {' >> /gen_config.py && \
    echo '  "username": os.environ.get("USERNAME"),' >> /gen_config.py && \
    echo '  "password": os.environ.get("PASSWORD"),' >> /gen_config.py && \
    echo '  "country": "IN",' >> /gen_config.py && \
    echo '  "language": "en",' >> /gen_config.py && \
    echo '  "trustedDeviceName": "KoyebBot",' >> /gen_config.py && \
    echo '  "acceptInvitations": True' >> /gen_config.py && \
    echo '}' >> /gen_config.py && \
    echo 'print(f"Generating Config for: {config.get("username")}")' >> /gen_config.py && \
    echo 'with open("/usr/src/app/config.json", "w") as f:' >> /gen_config.py && \
    echo '  json.dump(config, f, indent=2)' >> /gen_config.py

# 6. Create Startup Script
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'echo "--- STARTING BOT ---"' >> /start.sh && \
    echo 'echo "1. Generating Config..."' >> /start.sh && \
    echo 'python3 /gen_config.py' >> /start.sh && \
    echo 'echo "2. Starting Eufy Driver..."' >> /start.sh && \
    echo 'node dist/bin/server.js &' >> /start.sh && \
    echo 'echo "3. Waiting 20s for Driver Init..."' >> /start.sh && \
    echo 'sleep 20' >> /start.sh && \
    echo 'echo "4. Starting Python Bot..."' >> /start.sh && \
    echo 'python3 /main.py' >> /start.sh

RUN chmod +x /start.sh

# 7. Expose Ports & Run
EXPOSE 5000 8000
ENTRYPOINT []
CMD ["/start.sh"]
