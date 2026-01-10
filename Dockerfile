FROM bropat/eufy-security-ws:latest

RUN apk add --no-cache python3 py3-pip ffmpeg
RUN pip3 install requests pytz --break-system-packages

COPY main.py /app/main.py

# Startup Script: Bridge ko port 3000 denge aur Python ko 90s baad chalayenge
RUN echo -e "#!/bin/sh\nexport PORT=3000\n/usr/local/bin/docker-entrypoint.sh & sleep 90 && python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 3000

CMD ["/app/start.sh"]
