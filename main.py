import requests
import time
import os
from datetime import datetime
import pytz

# --- CONFIGURATION ---
# Port 8000 is final based on your working logs
KOYEB_URL = "http://localhost:8000" 
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = pytz.timezone('Asia/Kolkata')

def send_to_telegram(video_path):
    """Video ko Telegram par bhejne ka function"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    try:
        with open(video_path, 'rb') as f:
            payload = {'chat_id': CHAT_ID, 'caption': f'📹 CCTV Alert IST: {datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")}'}
            files = {'video': f}
            r = requests.post(url, data=payload, files=files)
            if r.status_code == 200:
                print(f"✅ Telegram par video bhej di gayi: {video_path}")
            else:
                print(f"❌ Telegram Error: {r.text}")
        
        # Bhejne ke baad file delete karein taaki storage na bhare
        if os.path.exists(video_path):
            os.remove(video_path)
    except Exception as e:
        print(f"❌ Telegram function mein error: {e}")

print("🚀 Monitoring System ACTIVE on Port 8000")

while True:
    now = datetime.now(IST)
    
    # --- INTERNAL ANTI-SLEEP HEARTBEAT ---
    # Yeh Koyeb ko traffic dikhayega taaki deep sleep na ho
    try:
        requests.get(KOYEB_URL, timeout=5)
    except:
        pass

    # Aapne testing ke liye ise 24 ghante (0-24) set kiya hai
    if 0 <= now.hour < 24:
        print(f"📸 Heartbeat Check: {now.strftime('%H:%M:%S')}")
        filename = f"rec_{int(time.time())}.mp4"
        
        # FFmpeg recording: localhost:8000 ka use
        # -loglevel error taaki logs saaf rahein
        status = os.system(f"ffmpeg -y -loglevel error -i {KOYEB_URL}/live_stream_link -t 30 -c copy {filename}")
        
        if status == 0 and os.path.exists(filename):
            print("✅ Video capture ho gaya! Telegram par bhej raha hoon...")
            send_to_telegram(filename)
            # Ek baar video milne ke baad 5 minute ka gap (300 seconds)
            time.sleep(300) 
        else:
            # Agar stream available nahi hai (motion nahi hai)
            print("⏳ Bridge connected hai, lekin camera stream nahi bhej raha (No Motion)...")
            time.sleep(60) 
    else:
        # Agar working hours se bahar ho
        time.sleep(60)
