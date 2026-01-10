import requests
import time
import os
from datetime import datetime
import pytz

# CONFIGURATION (Details Koyeb Dashboard mein bharenge)
# Bridge aur Recorder ab ek hi instance mein hain, isliye localhost use hoga
KOYEB_URL = "http://localhost:3000" 
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = pytz.timezone('Asia/Kolkata')

def send_to_telegram(video_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    try:
        with open(video_path, 'rb') as f:
            requests.post(url, data={'chat_id': CHAT_ID, 'caption': 'Raat ka Alert!'}, files={'video': f})
        os.remove(video_path)
    except Exception as e:
        print(f"Telegram Error: {e}")

print("All-in-One Monitoring started...")

while True:
    now_ist = datetime.now(IST)
    current_hour = now_ist.hour

    # Raat 12 AM se Subah 5 AM tak
    if 0 <= current_hour < 24:
        try:
            filename = f"eufy_{int(time.time())}.mp4"
            # FFmpeg clip recording
            os.system(f"ffmpeg -i {KOYEB_URL}/live_stream_link -t 30 -c copy {filename}")
            
            if os.path.exists(filename):
                send_to_telegram(filename)
                print(f"Video sent at {now_ist}")
        except Exception as e:
            print(f"Error: {e}")
    
    time.sleep(60)
