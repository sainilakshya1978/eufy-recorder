import requests
import time
import os
from datetime import datetime
import pytz

KOYEB_URL = "http://localhost:3000" 
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = pytz.timezone('Asia/Kolkata')

print("🚀 Monitoring System starting...")

# --- SMART WAIT LOOP ---
def wait_for_bridge():
    while True:
        try:
            # Hum check karenge ki kya bridge response de raha hai
            requests.get(KOYEB_URL, timeout=5)
            print("🟢 Bridge is now ACTIVE and READY!")
            return True
        except:
            print("⏳ Bridge is still starting... waiting 10 seconds.")
            time.sleep(10)

wait_for_bridge()

while True:
    now = datetime.now(IST)
    if 0 <= now.hour < 24: 
        filename = f"clip_{int(time.time())}.mp4"
        # Bridge ready hai, ab FFmpeg chalayenge
        status = os.system(f"ffmpeg -y -i {KOYEB_URL}/live_stream_link -t 30 -c copy {filename}")
        
        if status == 0 and os.path.exists(filename):
            # Telegram upload logic yahan aayega
            print("✅ Video captured successfully!")
            time.sleep(300) # 5 min gap
        else:
            print("⚠️ Stream busy, retrying in 60s...")
            time.sleep(60)
