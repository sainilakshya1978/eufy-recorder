FROM bropat/eufy-security-ws:latest

# Flask aur baki libraries ko install karein
RUN apk add --no-cache python3 py3-pip ffmpeg
RUN pip3 install requests pyTelegramBotAPI websocket-client flask --break-system-packages

COPY main.py /app/main.py

# Bridge ko start hone ka time dena (Grace Period)
RUN echo -e "#!/bin/sh\n/usr/local/bin/docker-entrypoint.sh & sleep 90 && python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
