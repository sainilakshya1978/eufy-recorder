FROM bropat/eufy-security-ws:latest

RUN apk add --no-cache python3 py3-pip ffmpeg
RUN pip3 install pyTelegramBotAPI websocket-client flask --break-system-packages

COPY main.py /app/main.py

# Koyeb ko ye dono ports chahiye
EXPOSE 5000
EXPOSE 8000

# Driver start -> Wait -> Python Bot
CMD ["/bin/sh", "-c", "/usr/local/bin/docker-entrypoint.sh & sleep 60 && python3 /app/main.py"]
