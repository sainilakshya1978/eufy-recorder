FROM bropat/eufy-security-ws:latest

# Python aur FFMPEG (Video processing ke liye) install karein
RUN apk add --no-cache python3 py3-pip ffmpeg
RUN pip3 install pyTelegramBotAPI websocket-client --break-system-packages

COPY main.py /app/main.py

# Important: Port 8000 internal communication ke liye
EXPOSE 8000

# Script: Driver start -> Wait 60s -> Bot start
CMD ["/bin/sh", "-c", "/usr/local/bin/docker-entrypoint.sh & sleep 60 && python3 /app/main.py"]
