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
            response = requests.post(url, data={'chat_id': CHAT_ID, 'caption': 'CCTV Raat ka Alert!'}, files={'video': f})
        if response.status_code == 200:
            print(f"✅ Video sent: {video_path}")
            os.remove(video_path)
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

print("🚀 Monitoring System starting...")

# Bridge ko login aur setup hone ke liye pehla lamba wait
time.sleep(90) 

while True:
    now_ist = datetime.now(IST)
    current_hour = now_ist.hour

    # TESTING: 0-24 tak (Deployment check ke liye)
    if 0 <= current_hour < 24:
        print(f"📸 Trying to record stream: {now_ist.strftime('%H:%M:%S')}")
        filename = f"eufy_clip_{int(time.time())}.mp4"
        
        # FFmpeg command
        # -re command add kiya hai taaki stream sync rahe
        status = os.system(f"ffmpeg -y -i {KOYEB_URL}/live_stream_link -t 30 -c copy {filename}")
        
        if status == 0 and os.path.exists(filename):
            send_to_telegram(filename)
            print("⏳ Next check in 5 minutes...")
            time.sleep(300) # Ek baar video mil jaye toh 5 min wait karega
        else:
            print("⚠️ Bridge abhi tak ready nahi hai. 60 seconds mein fir try karenge...")
            time.sleep(60)
    else:
        time.sleep(60)
