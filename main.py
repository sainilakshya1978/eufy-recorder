import requests
import time
import os
from datetime import datetime
import pytz

# Port 8000 logs ke mutabik
KOYEB_URL = "http://localhost:8000" 
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = pytz.timezone('Asia/Kolkata')

def send_to_telegram(video_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    try:
        with open(video_path, 'rb') as f:
            res = requests.post(url, data={'chat_id': CHAT_ID, 'caption': 'CCTV Alert!'}, files={'video': f})
        if res.status_code == 200:
            print(f"✅ Video Sent")
            os.remove(video_path)
    except Exception as e:
        print(f"❌ Error: {e}")

print("🚀 Monitoring Started on Port 8000...")

while True:
    now = datetime.now(IST)
    
    # Har loop mein bridge ko ping karein taaki Koyeb active rahe
    try:
        requests.get(KOYEB_URL, timeout=5)
    except:
        pass

    if 0 <= now.hour < 24:
        print(f"📸 Checking: {now.strftime('%H:%M:%S')}")
        filename = f"clip_{int(time.time())}.mp4"
        
        # FFmpeg command
        status = os.system(f"ffmpeg -y -i {KOYEB_URL}/live_stream_link -t 30 -c copy {filename}")
        
        if status == 0 and os.path.exists(filename):
            send_to_telegram(filename)
            time.sleep(300) # Success ke baad 5 min wait
        else:
            print("⚠️ Waiting for stream...")
            time.sleep(60)
    else:
        time.sleep(60)
