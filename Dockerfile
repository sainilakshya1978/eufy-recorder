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

# 5. Startup Script (With Debug Logging enabled)
#    Humne "DEBUG=*" add kiya hai taaki Eufy ke errors dikh sakein
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'echo "Creating config.json..."' >> /start.sh && \
    echo 'echo "{' >> /start.sh && \
    echo '  \"username\": \"$USERNAME\",' >> /start.sh && \
    echo '  \"password\": \"$PASSWORD\",' >> /start.sh && \
    echo '  \"country\": \"$COUNTRY\",' >> /start.sh && \
    echo '  \"language\": \"en\",' >> /start.sh && \
    echo '  \"trustedDeviceName\": \"${TRUSTED_DEVICE_NAME:-KoyebBot}\",' >> /start.sh && \
    echo '  \"acceptInvitations\": true' >> /start.sh && \
    echo '}" > /usr/src/app/config.json' >> /start.sh && \
    echo 'echo "--------------------------------------"' >> /start.sh && \
    echo 'echo "STARTING EUFY DRIVER WITH LOGS..."' >> /start.sh && \
    echo 'echo "--------------------------------------"' >> /start.sh && \
    echo '# Node ko foreground me chalayenge thodi der logs dekhne ke liye' >> /start.sh && \
    echo 'export DEBUG=eufy-security-client*' >> /start.sh && \
    echo 'node dist/bin/server.js 2>&1 > /var/log/eufy_driver.log & ' >> /start.sh && \
    echo 'tail -f /var/log/eufy_driver.log & ' >> /start.sh && \
    echo 'sleep 10' >> /start.sh && \
    echo 'echo "Starting Python Logic..."' >> /start.sh && \
    echo 'python3 /main.py' >> /start.sh

RUN chmod +x /start.sh

EXPOSE 5000 8000

ENTRYPOINT []
CMD ["/start.sh"]
