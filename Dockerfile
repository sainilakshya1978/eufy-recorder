FROM bropat/eufy-security-ws:latest

RUN apk add --no-cache python3 py3-pip ffmpeg
RUN pip3 install requests pytz --break-system-packages

COPY main.py /app/main.py

# Bridge ko PORT 3000 par force karenge aur Python ko 100s ka headstart denge
RUN echo -e "#!/bin/sh\nexport PORT=3000\n/usr/local/bin/docker-entrypoint.sh & sleep 100 && python3 /app/main.py" > /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 3000

CMD ["/app/start.sh"]
