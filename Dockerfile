FROM bropat/eufy-security-ws:latest

# 1. Install Python, FFmpeg and other tools
RUN apk add --no-cache python3 py3-pip ffmpeg

# 2. Virtual Environment Setup
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Install Python Libraries
RUN pip install pyTelegramBotAPI websocket-client flask

# 4. Copy main.py to root
COPY main.py /main.py

# 5. Create a Startup Script to generate config.json manually
#    Yeh script environment variables se config file banayegi
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'echo "Creating config.json from Environment Variables..."' >> /start.sh && \
    echo 'echo "{' >> /start.sh && \
    echo '  \"username\": \"$USERNAME\",' >> /start.sh && \
    echo '  \"password\": \"$PASSWORD\",' >> /start.sh && \
    echo '  \"country\": \"$COUNTRY\",' >> /start.sh && \
    echo '  \"language\": \"en\",' >> /start.sh && \
    echo '  \"trustedDeviceName\": \"${TRUSTED_DEVICE_NAME:-KoyebBot}\",' >> /start.sh && \
    echo '  \"acceptInvitations\": true' >> /start.sh && \
    echo '}" > /usr/src/app/config.json' >> /start.sh && \
    echo 'echo "Starting Node.js Driver..."' >> /start.sh && \
    echo 'node dist/bin/server.js &' >> /start.sh && \
    echo 'echo "Waiting 15s for Driver init..."' >> /start.sh && \
    echo 'sleep 15' >> /start.sh && \
    echo 'echo "Starting Python Bot..."' >> /start.sh && \
    echo 'python3 /main.py' >> /start.sh

# 6. Permissions setup
RUN chmod +x /start.sh

# 7. Expose Ports
EXPOSE 5000
EXPOSE 8000

# 8. Reset Entrypoint and run our script
ENTRYPOINT []
CMD ["/start.sh"]
