FROM bropat/eufy-security-ws:latest

RUN apk add --no-cache python3 py3-pip ffmpeg
RUN pip3 install requests pytz pyTelegramBotAPI --break-system-packages

COPY main.py /app/main.py

# Bridge startup ke liye 90s ka wait (Connection Refused fix karne ke liye)
RUN echo -e "#!/bin/sh\n/usr/local/bin/docker-entrypoint.sh & sleep 90 && python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
