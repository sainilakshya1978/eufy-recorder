FROM bropat/eufy-security-ws:latest

# Python aur zaruri libraries install karein
RUN apk add --no-cache python3 py3-pip ffmpeg
RUN pip3 install requests pyTelegramBotAPI websocket-client flask --break-system-packages

COPY main.py /app/main.py

# Koyeb ke liye ports open karein
EXPOSE 8000
EXPOSE 5000

# Start script: Driver start hoga, 30 sec wait karega, phir bot start hoga
RUN echo -e "#!/bin/sh\n/usr/local/bin/docker-entrypoint.sh & sleep 30 && python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
