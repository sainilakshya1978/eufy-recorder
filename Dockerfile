FROM bropat/eufy-security-ws:latest

# 1. Install necessary tools
RUN apk add --no-cache python3 py3-pip ffmpeg

# 2. Install Python libraries
RUN pip3 install requests pytz --break-system-packages

# 3. Copy your script
COPY main.py /app/main.py

# 4. Startup Script: Force Bridge to port 3000 and wait for it
RUN echo -e "#!/bin/sh\n/usr/local/bin/docker-entrypoint.sh --port 3000 & sleep 60 && python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

# 5. Expose Port 3000 for Koyeb Health Check
EXPOSE 3000

CMD ["/app/start.sh"]
