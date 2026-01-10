import requests
import time
import os
from datetime import datetime
import pytz

# CONFIGURATION: Aligning to Port 8000
KOYEB_URL = "http://localhost:8000" 
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = pytz.timezone('Asia/Kolkata')

def send_to_telegram(video_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    try:
        with open(video_path, 'rb') as f:
            requests.post(url, data={'chat_id': CHAT_ID, 'caption': 'CCTV Alert!'}, files={'video': f})
        os.remove(video_path)
        print("✅ Telegram Video Sent!")
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

print("🚀 System Starting... Connecting to Port 8000...")

# --- WAIT LOOP: Keep trying until Port 8000 is ready ---
while True:
    try:
        requests.get(KOYEB_URL, timeout=5)
        print("🟢 Bridge (Port 8000) Connected Successfully!")
        break
    except:
        print("⏳ Waiting for Bridge on Port 8000... (Retrying in 5s)")
        time.sleep(5)

# --- RECORDING LOOP ---
while True:
    now = datetime.now(IST)
    
    # Keep-Alive: Ping the server to keep the connection warm
    try:
        requests.get(KOYEB_URL, timeout=2)
    except:
        pass

    if 0 <= now.hour < 24: 
        filename = f"clip_{int(time.time())}.mp4"
        
        # FFmpeg pointing to Port 8000
        status = os.system(f"ffmpeg -y -i {KOYEB_URL}/live_stream_link -t 30 -c copy {filename}")
        
        if status == 0 and os.path.exists(filename):
            send_to_telegram(filename)
            time.sleep(300) # Wait 5 mins after a success
        else:
            print("⚠️ Stream not ready. Retrying in 60s...")
            time.sleep(60)
    else:
        time.sleep(60)
