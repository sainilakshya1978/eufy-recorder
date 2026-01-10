FROM bropat/eufy-security-ws:latest

# 1. Python, FFmpeg aur dependencies install karein
RUN apk add --no-cache python3 py3-pip ffmpeg

# 2. Python Libraries (pyTelegramBotAPI status command ke liye)
RUN pip3 install requests pytz pyTelegramBotAPI --break-system-packages

# 3. Copy main.py
COPY main.py /app/main.py

# 4. Modified Startup Logic (Added more sleep for stability)
# Bridge ko start hone ke liye 60 seconds diye hain taaki "Connection Refused" error na aaye
RUN echo -e "#!/bin/sh\n/usr/local/bin/docker-entrypoint.sh & sleep 60 && python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

# 5. Port 8000 expose karein
# Make sure Koyeb Dashboard par bhi yahi port set ho
EXPOSE 8000

CMD ["/app/start.sh"]
