FROM bropat/eufy-security-ws:latest

# Dependencies install karein
RUN apk add --no-cache python3 py3-pip ffmpeg

# Virtual environment use karein (Best practice)
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install pyTelegramBotAPI websocket-client flask

# App directory setup
WORKDIR /app
COPY main.py /app/main.py

# Ports
EXPOSE 5000
EXPOSE 8000

# ENTRYPOINT को reset karke seedha command chalayein
ENTRYPOINT []
CMD ["/bin/sh", "-c", "/usr/local/bin/docker-entrypoint.sh node src/bin/server.js & python3 /app/main.py"]
