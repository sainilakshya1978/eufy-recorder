FROM bropat/eufy-security-ws:latest

# Basic tools
RUN apk add --no-cache python3 py3-pip ffmpeg
RUN pip3 install pyTelegramBotAPI websocket-client flask --break-system-packages

COPY main.py /app/main.py

# Expose ports
EXPOSE 8000
EXPOSE 5000

# Start script: Driver start -> Wait 60s -> Bot start
RUN echo -e "#!/bin/sh\n/usr/local/bin/docker-entrypoint.sh & sleep 60 && python3 /app/main.py" > /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
