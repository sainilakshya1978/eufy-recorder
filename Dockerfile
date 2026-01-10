FROM bropat/eufy-security-ws:latest

# Python aur FFmpeg install karein
RUN apk add --no-cache python3 py3-pip ffmpeg

# Libraries install karein
RUN pip3 install requests pytz --break-system-packages

# Apni script copy karein
COPY main.py /app/main.py

# Startup script: 60 seconds ka wait taaki bridge ready ho jaye
RUN echo -e "#!/bin/sh\n/usr/local/bin/docker-entrypoint.sh & sleep 60 && python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

# Port 3000 expose karein
EXPOSE 3000

CMD ["/app/start.sh"]
