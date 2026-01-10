import requests
import time
import os
from datetime import datetime
import pytz

# PORT 8000 IS FINAL
KOYEB_URL = "http://localhost:8000" 
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = pytz.timezone('Asia/Kolkata')

print("🚀 Monitoring System ACTIVE on Port 8000")

while True:
    now = datetime.now(IST)
    
    # --- KEEP ALIVE PING ---
    # Yeh Koyeb ko traffic dikhayega taaki deep sleep na ho
    try:
        requests.get(KOYEB_URL, timeout=5)
    except:
        pass

    # Raat ke time recording (ya testing ke liye 0-24)
    if 0 <= now.hour < 24:
        print(f"📸 Heartbeat Check: {now.strftime('%H:%M:%S')}")
        filename = f"rec_{int(time.time())}.mp4"
        
        # FFmpeg recording
        status = os.system(f"ffmpeg -y -loglevel error -i {KOYEB_URL}/live_stream_link -t 30 -c copy {filename}")
        
        if status == 0 and os.path.exists(filename):
            # Telegram code...
            print("✅ Video captured!")
            time.sleep(300) # 5 minute gap
        else:
            print("⏳ Bridge is connected, waiting for motion/stream...")
            time.sleep(60) 
    else:
        time.sleep(60)
