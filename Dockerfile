# 1. Bridge ka image uthayein
FROM bropat/eufy-security-ws:latest

# 2. Python aur FFmpeg install karein (Typo fixed here)
RUN apk add --no-cache python3 py3-pip ffmpeg

# 3. Python libraries install karein
RUN pip3 install requests pytz --break-system-packages

# 4. Apni script ko copy karein
COPY main.py /app/main.py

# 5. Startup script banayein
RUN echo -e "#!/bin/sh\nnode src/main.js & python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

# 6. Run karein
CMD ["/app/start.sh"]
