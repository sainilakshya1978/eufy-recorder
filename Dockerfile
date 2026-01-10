FROM bropat/eufy-security-ws:latest

# Tools install karein
RUN apk add --no-cache python3 py3-pip ffmpeg

# Libraries install karein
RUN pip3 install requests pytz --break-system-packages

# Script copy karein
COPY main.py /app/main.py

# Startup: Bridge ko port 3000 par start karega aur 60s wait karega
RUN echo -e "#!/bin/sh\n/usr/local/bin/docker-entrypoint.sh --port 3000 & sleep 60 && python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

# Port 3000 expose karein
EXPOSE 3000

CMD ["/app/start.sh"]
