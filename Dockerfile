FROM bropat/eufy-security-ws:latest

# Build-time dependencies
RUN apk add --no-cache python3 py3-pip ffmpeg

# Create virtual environment to avoid --break-system-packages issues
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip3 install pyTelegramBotAPI websocket-client flask

COPY main.py /app/main.py

EXPOSE 5000
EXPOSE 8000

# Script create karein jo dono ko manage kare
RUN echo "#!/bin/sh\n/usr/local/bin/docker-entrypoint.sh & \nsleep 10\npython3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
