import requests
import time
import os
from datetime import datetime
import pytz

KOYEB_URL = "http://localhost:3000" 
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = pytz.timezone('Asia/Kolkata')

def send_to_telegram(video_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    try:
        with open(video_path, 'rb') as f:
            requests.post(url, data={'chat_id': CHAT_ID, 'caption': 'CCTV Alert!'}, files={'video': f})
        os.remove(video_path)
        print(f"✅ Video Sent Successfully!")
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

print("🚀 Starting System... Waiting for Bridge to be ready.")

# --- NAYA WAIT LOGIC ---
while True:
    try:
        # Check if bridge is responding
        response = requests.get(KOYEB_URL, timeout=5)
        print("🟢 Bridge is UP and Running!")
        break
    except:
        print("⏳ Bridge starting... waiting 10 more seconds.")
        time.sleep(10)

while True:
    now = datetime.now(IST)
    if 0 <= now.hour < 24: # Testing ke liye full day
        filename = f"eufy_{int(time.time())}.mp4"
        # FFmpeg with 'reconnect' flags for stability
        status = os.system(f"ffmpeg -y -i {KOYEB_URL}/live_stream_link -t 30 -c copy {filename}")
        
        if status == 0 and os.path.exists(filename):
            send_to_telegram(filename)
            time.sleep(300) # Ek clip ke baad 5 min ka gap
        else:
            print("⚠️ Stream busy or not found. Retrying in 60s...")
            time.sleep(60)
    else:
        time.sleep(60)
