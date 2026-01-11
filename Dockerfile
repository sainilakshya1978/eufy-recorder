FROM bropat/eufy-security-ws:latest

# 1. Install Python and dependencies
RUN apk add --no-cache python3 py3-pip ffmpeg

# 2. Virtual Environment setup (System packages break hone se bachane ke liye)
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Install Python Libraries
RUN pip install pyTelegramBotAPI websocket-client flask

# 4. Copy main.py to root (Isse Eufy ka folder structure kharab nahi hoga)
COPY main.py /main.py

# 5. Ports expose karein
EXPOSE 5000
EXPOSE 8000

# 6. Command
# Hum 'dist/bin/server.js' use karenge jo sahi compiled file hai
# 'sleep 10' ensure karega ki Node server pehle start ho
CMD ["/bin/sh", "-c", "node dist/bin/server.js & sleep 10 && python3 /main.py"]
