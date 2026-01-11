FROM bropat/eufy-security-ws:latest

# Environment setup
ENV PORT=8000

# Install Dependencies
RUN apk add --no-cache python3 py3-pip ffmpeg
RUN pip3 install requests pyTelegramBotAPI websocket-client flask --break-system-packages

# Copy Code
COPY main.py /app/main.py

# Expose Ports (5000 Flask, 8000 Camera)
EXPOSE 5000
EXPOSE 8000

# Final Command: Driver start karo -> Wait karo -> Python chalao
CMD ["/bin/sh", "-c", "/usr/local/bin/docker-entrypoint.sh & sleep 20 && python3 /app/main.py"]
