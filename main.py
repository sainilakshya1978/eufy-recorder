import requests
import time
import os
from datetime import datetime
import pytz

# CONFIG
KOYEB_URL = "http://localhost:3000" 
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = pytz.timezone('Asia/Kolkata')

def send_to_telegram(video_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    try:
        with open(video_path, 'rb') as f:
            res = requests.post(url, data={'chat_id': CHAT_ID, 'caption': 'CCTV Alert!'}, files={'video': f})
        if res.status_code == 200:
            print(f"✅ Sent: {video_path}")
            os.remove(video_path)
    except Exception as e:
        print(f"❌ Error: {e}")

print("🚀 System Starting... Waiting for Bridge...")
time.sleep(20) # Extra wait

while True:
    now = datetime.now(IST)
    # TEST MODE: 0 se 24 (Har waqt check karega)
    if 0 <= now.hour < 24:
        print(f"📸 Checking Stream: {now.strftime('%H:%M:%S')}")
        filename = f"clip_{int(time.time())}.mp4"
        # FFmpeg command
        status = os.system(f"ffmpeg -y -i {KOYEB_URL}/live_stream_link -t 30 -c copy {filename}")
        
        if status == 0 and os.path.exists(filename):
            send_to_telegram(filename)
        else:
            print("⚠️ Bridge not ready or no motion. Retrying...")
            
    time.sleep(60)
