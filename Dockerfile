FROM bropat/eufy-security-ws:latest

# 1. Install Python, Pip and FFmpeg
RUN apk add --no-cache python3 py3-pip ffmpeg

# 2. Install Libraries
RUN pip3 install requests pytz --break-system-packages

# 3. Copy main.py to /app
COPY main.py /app/main.py

# 4. Create Startup Script (Fixing the --port error)
# Hum environment variable PORT ka use karenge
RUN echo -e "#!/bin/sh\nexport PORT=3000\n/usr/local/bin/docker-entrypoint.sh & sleep 60 && python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

# 5. Expose port 3000 for Koyeb
EXPOSE 3000

CMD ["/app/start.sh"]
