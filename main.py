import requests
import time
import os
from datetime import datetime
import pytz # India time ke liye

# CONFIGURATION
# In brackets mein sirf NAAM rehne dein, asli details Koyeb Dashboard mein bharenge
KOYEB_URL = os.getenv("KOYEB_BRIDGE_URL") 
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = pytz.timezone('Asia/Kolkata')

def send_to_telegram(video_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    with open(video_path, 'rb') as f:
        requests.post(url, data={'chat_id': CHAT_ID, 'caption': 'Raat ka Alert!'}, files={'video': f})
    os.remove(video_path)

print("Monitoring started...")

while True:
    # India ka sahi time nikalna
    now_ist = datetime.now(IST)
    current_hour = now_ist.hour

    # Raat 12 AM (0) se Subah 5 AM (5) tak check karega
    if 0 <= current_hour < 5:
        try:
            # 1. Eufy Bridge se check karna ki koi movement hai ya nahi
            # (Note: Agar bridge direct stream de raha hai toh hum FFmpeg chalayenge)
            filename = f"eufy_{int(time.time())}.mp4"
            
            # FFmpeg Command: 30 seconds ki clip record karega
            # Ye command Koyeb server ke andar hi chalegi
            os.system(f"ffmpeg -i {KOYEB_URL}/live_stream_link -t 30 -c copy {filename}")
            
            if os.path.exists(filename):
                send_to_telegram(filename)
                print(f"Video sent at {now_ist}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    # Har 1 minute mein check karega taaki server par load na bade
    time.sleep(60)
