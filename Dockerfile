FROM bropat/eufy-security-ws:latest

# WebSocket client aur dependencies install karein
RUN apk add --no-cache python3 py3-pip ffmpeg
RUN pip3 install requests pyTelegramBotAPI websocket-client --break-system-packages

COPY main.py /app/main.py

# Bridge ko 90s ka time dena taaki "Connection Refused" na aaye
RUN echo -e "#!/bin/sh\n/usr/local/bin/docker-entrypoint.sh & sleep 90 && python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

# Port 8000 expose karna
EXPOSE 8000

CMD ["/app/start.sh"]
