FROM bropat/eufy-security-ws:latest

RUN apk add --no-cache python3 py3-pip ffmpeg
RUN pip3 install pyTelegramBotAPI websocket-client flask --break-system-packages

COPY main.py /app/main.py

EXPOSE 5000
EXPOSE 8000

# Driver ko background mein start karke python ko shuru karna
CMD ["/bin/sh", "-c", "/usr/local/bin/docker-entrypoint.sh & python3 /app/main.py"]
