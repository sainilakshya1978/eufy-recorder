FROM bropat/eufy-security-ws:latest

# 1. Environment Variables set karein taaki logs dikhein
ENV PORT=8000
ENV HOST=0.0.0.0

# 2. Python aur dependencies install karein
RUN apk add --no-cache python3 py3-pip ffmpeg
RUN pip3 install requests pyTelegramBotAPI websocket-client flask --break-system-packages

# 3. Main file copy karein
COPY main.py /app/main.py

# 4. Permissions set karein (Zaroori step)
# Eufy driver ko data save karne ke liye permission chahiye hoti hai
RUN mkdir -p /data && chmod 777 /data

# 5. Ports expose karein
EXPOSE 8000
EXPOSE 5000

# 6. Robust Start Script
# Hum ek temporary script banayenge jo pehle Driver ko chalayega, fir wait karega, fir Python ko
RUN echo -e "#!/bin/sh\n\
echo '🚀 Starting Eufy Security Bridge...'\n\
/usr/local/bin/docker-entrypoint.sh > /var/log/eufy.log 2>&1 &\n\
echo '⏳ Waiting 20 seconds for Driver to initialize...'\n\
sleep 20\n\
echo '🐍 Starting Python Bot...'\n\
python3 /app/main.py" > /app/run.sh

RUN chmod +x /app/run.sh

CMD ["/app/run.sh"]
