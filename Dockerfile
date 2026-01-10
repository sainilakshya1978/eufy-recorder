FROM bropat/eufy-security-ws:latest

# 1. Install Python, FFmpeg and dependencies
RUN apk add --no-cache python3 py3-pip ffmpeg

# 2. Install Python Libraries (Added pyTelegramBotAPI for /status)
RUN pip3 install requests pytz pyTelegramBotAPI --break-system-packages

# 3. Copy the script
COPY main.py /app/main.py

# 4. Startup Script
# Bridge ko 30s milte hain connect hone ke liye
RUN echo -e "#!/bin/sh\n/usr/local/bin/docker-entrypoint.sh & sleep 30 && python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

# 5. Native Port 8000 expose karein
EXPOSE 8000

CMD ["/app/start.sh"]
