FROM bropat/eufy-security-ws:latest

# 1. Install Tools
RUN apk add --no-cache python3 py3-pip ffmpeg

# 2. Install Libraries
RUN pip3 install requests pytz --break-system-packages

# 3. Copy Script
COPY main.py /app/main.py

# 4. Startup Script: Note - No custom PORT variable. Standard launch.
# Python ko 30s delay denge taaki Bridge 8000 par ready ho jaye
RUN echo -e "#!/bin/sh\n/usr/local/bin/docker-entrypoint.sh & sleep 30 && python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

# 5. Expose Port 8000 (Important)
EXPOSE 8000

CMD ["/app/start.sh"]
