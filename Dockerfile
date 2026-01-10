FROM bropat/eufy-security-ws:latest

# 1. Install Python and FFmpeg
RUN apk add --no-cache python3 py3-pip ffmpeg

# 2. Install Python Libraries
RUN pip3 install requests pytz --break-system-packages

# 3. Copy the script
COPY main.py /app/main.py

# 4. Startup Script
# We give the bridge 30 seconds to start before running Python
RUN echo -e "#!/bin/sh\n/usr/local/bin/docker-entrypoint.sh & sleep 30 && python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

# 5. Expose Port 8000 (The native Eufy port)
EXPOSE 8000

CMD ["/app/start.sh"]
