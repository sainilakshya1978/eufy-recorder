import requests
import time
import os
from datetime import datetime
import pytz

# CONFIGURATION
# Ab dono ek hi server par hain, isliye localhost use hoga
KOYEB_URL = "http://localhost:3000" 
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = pytz.timezone('Asia/Kolkata')

def send_to_telegram(video_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    try:
        with open(video_path, 'rb') as f:
            response = requests.post(url, data={'chat_id': CHAT_ID, 'caption': 'Raat ka Alert!'}, files={'video': f})
        if response.status_code == 200:
            print(f"✅ Video sent successfully: {video_path}")
            os.remove(video_path)
        else:
            print(f"❌ Telegram Error: {response.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

print("🚀 All-in-One Monitoring System Starting...")

# Bridge ko fully load hone ke liye thoda extra time dena
time.sleep(15) 

while True:
    now_ist = datetime.now(IST)
    current_hour = now_ist.hour

    # TESTING MODE: Abhi 0 se 24 rakha hai taaki turant check ho sake.
    # Sab sahi chalne par ise 0 se 5 kar dena.
    if 0 <= current_hour < 24:
        print(f"📸 Checking stream at {now_ist.strftime('%H:%M:%S')}...")
        
        filename = f"eufy_{int(time.time())}.mp4"
        
        # FFmpeg command: 30 seconds ki clip record karega
        # -t 30 matlab 30 seconds
        status = os.system(f"ffmpeg -y -i {KOYEB_URL}/live_stream_link -t 30 -c copy {filename}")
        
        if status == 0 and os.path.exists(filename):
            send_to_telegram(filename)
        else:
            print("⚠️ Bridge ready nahi hai ya stream nahi mili. 1 minute baad fir koshish karenge...")
    
    # Har 1 minute baad check karega
    time.sleep(60)
