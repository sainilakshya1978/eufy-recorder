# 1. Pehle Bridge ka image uthayein
FROM bropat/eufy-security-ws:latest

# 2. Python aur FFmpeg install karein (recording ke liye)
RUN apk add --no-run-if-empty python3 py3-pip ffmpeg

# 3. Python libraries install karein
RUN pip3 install requests pytz --break-system-packages

# 4. Apni script ko andar copy karein
COPY main.py /app/main.py

# 5. Ek startup script banayein jo dono ko saath chalaye
RUN echo "#!/bin/sh\nnode src/main.js & python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

# 6. Is script ko run karein
CMD ["/app/start.sh"]
