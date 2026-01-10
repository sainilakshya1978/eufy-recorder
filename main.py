import requests
import time
import os
from datetime import datetime
import pytz

# --- CONFIGURATION ---
# Port 8000 is native to Eufy Bridge logs
KOYEB_URL = "http://localhost:8000" 
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = pytz.timezone('Asia/Kolkata')

def send_to_telegram(video_path):
    """High Quality Video aur Detailed Caption ke saath Telegram par bhejna"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    current_time = datetime.now(IST).strftime("%I:%M:%S %p")
    current_date = datetime.now(IST).strftime("%d-%m-%Y")
    
    try:
        with open(video_path, 'rb') as f:
            payload = {
                'chat_id': CHAT_ID, 
                'caption': f'🚨 **Motion Alert!**\n📅 Date: {current_date}\n⏰ Time: {current_time}\n📍 Status: Recorded on Koyeb',
                'parse_mode': 'Markdown'
            }
            files = {'video': f}
            r = requests.post(url, data=payload, files=files)
            
            if r.status_code == 200:
                print(f"✅ Success: Telegram par video bhej di gayi ({current_time})")
            else:
                print(f"❌ Telegram Error: {r.text}")
        
        # Cleanup: File delete karein taaki storage full na ho
        if os.path.exists(video_path):
            os.remove(video_path)
    except Exception as e:
        print(f"❌ Error in send_to_telegram: {e}")

print("🚀 System Starting: Monitoring Eufy Station on Port 8000...")

# --- INITIAL CONNECTION WAIT ---
# Bridge ko puri tarah se start hone ke liye wait loop
while True:
    try:
        requests.get(KOYEB_URL, timeout=5)
        print("🟢 Bridge is Online! Starting monitoring loop...")
        break
    except:
        print("⏳ Waiting for Bridge to respond on Port 8000...")
        time.sleep(10)

while True:
    now = datetime.now(IST)
    
    # --- INTERNAL ANTI-SLEEP HEARTBEAT ---
    # Har loop mein Koyeb ko signal bhejna taaki deep sleep na ho
    try:
        requests.get(KOYEB_URL, timeout=2)
    except:
        pass

    # 24/7 Monitoring (Night alerts ke liye hour range badal sakte hain)
    if 0 <= now.hour < 24:
        filename = f"cctv_{int(time.time())}.mp4"
        
        # --- BEST PRACTICE FFmpeg COMMAND ---
        # 1. libx264: Telegram compatible high quality video
        # 2. -preset ultrafast: CPU load kam karne ke liye
        # 3. -t 30: 30 seconds ka clip
        ffmpeg_cmd = (
            f"ffmpeg -y -loglevel error -i {KOYEB_URL}/live_stream_link "
            f"-t 30 -c:v libx264 -preset ultrafast -crf 28 -c:a aac {filename}"
        )
        
        status = os.system(ffmpeg_cmd)
        
        if status == 0 and os.path.exists(filename):
            print(f"✅ Clip Captured: {filename}")
            send_to_telegram(filename)
            # Video milne ke baad 5 min ka intezaar (spam rokne ke liye)
            time.sleep(300) 
        else:
            # Agar motion nahi hai ya connection timeout hai
            print(f"🔍 Checking... (No active stream at {now.strftime('%H:%M:%S')})")
            time.sleep(60) 
    else:
        time.sleep(60)
