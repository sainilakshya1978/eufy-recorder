FROM bropat/eufy-security-ws:latest
RUN apk add --no-cache python3 py3-pip ffmpeg
RUN pip3 install requests pytz --break-system-packages
COPY main.py /app/main.py

# Startup: Port 8000 fix
RUN echo -e "#!/bin/sh\n/usr/local/bin/docker-entrypoint.sh & sleep 60 && python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8000
CMD ["/app/start.sh"]
