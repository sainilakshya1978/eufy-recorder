FROM bropat/eufy-security-ws:latest

# 1. Install Python and FFmpeg
RUN apk add --no-cache python3 py3-pip ffmpeg

# 2. Virtual Environment Setup
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Install Python Libraries
RUN pip install pyTelegramBotAPI websocket-client flask

# 4. Copy main.py to root (Isse Eufy ka folder structure kharab nahi hoga)
COPY main.py /main.py

# 5. Expose Ports
EXPOSE 5000
EXPOSE 8000

# 6. CRITICAL FIX:
# Hum Entrypoint ko blank kar rahe hain taaki bropat ka default script na chale
ENTRYPOINT []

# 7. Start Command:
# Note: Hum 'node dist/bin/server.js' chala rahe hain jo sahi file hai.
CMD ["/bin/sh", "-c", "node dist/bin/server.js & sleep 15 && python3 /main.py"]
