import requests
import time
import os
from datetime import datetime
import pytz

# CONFIGURATION
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
        print("✅ Telegram par video bhej di gayi hai!")
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

print("🚀 System start ho raha hai... Bridge ka intezaar...")

# SMART WAIT LOOP: Jab tak server active nahi hota, intezaar karein
while True:
    try:
        response = requests.get(KOYEB_URL, timeout=5)
        print("🟢 Bridge fully active ho gaya hai!")
        break
    except:
        print("⏳ Bridge abhi login kar raha hai... 10 seconds mein fir check karenge.")
        time.sleep(10)

while True:
    now = datetime.now(IST)
    if 0 <= now.hour < 24: 
        filename = f"clip_{int(time.time())}.mp4"
        # FFmpeg command
        status = os.system(f"ffmpeg -y -i {KOYEB_URL}/live_stream_link -t 30 -c copy {filename}")
        
        if status == 0 and os.path.exists(filename):
            send_to_telegram(filename)
            time.sleep(300) # 5 min ka gap
        else:
            print("⚠️ Stream abhi busy hai. 60 seconds mein retry...")
            time.sleep(60)
    else:
        time.sleep(60)
