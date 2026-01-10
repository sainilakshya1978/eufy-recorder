import requests
import time
import os
from datetime import datetime
import pytz

# CONFIGURATION
# Localhost use hoga kyunki dono ek hi container mein hain
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
            print(f"✅ Video sent to Telegram: {video_path}")
            os.remove(video_path)
        else:
            print(f"❌ Telegram API Error: {response.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

print("🚀 All-in-One Monitoring System Started...")

while True:
    now_ist = datetime.now(IST)
    current_hour = now_ist.hour

    # TESTING MODE: 0-24 (Har waqt check karega)
    # Baad mein ise 0-5 kar dena (Raat ke liye)
    if 0 <= current_hour < 24:
        print(f"📸 Checking Stream at {now_ist.strftime('%H:%M:%S')}...")
        filename = f"eufy_clip_{int(time.time())}.mp4"
        
        # FFmpeg command: 30 seconds recording
        status = os.system(f"ffmpeg -y -i {KOYEB_URL}/live_stream_link -t 30 -c copy {filename}")
        
        if status == 0 and os.path.exists(filename):
            send_to_telegram(filename)
        else:
            print("⚠️ Bridge not ready yet or No Stream. Retrying in 60s...")
    
    time.sleep(60)
