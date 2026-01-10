import requests
import time
import os
import telebot
from datetime import datetime
import pytz
import threading

# --- CONFIGURATION ---
KOYEB_URL = "http://localhost:8000" 
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = pytz.timezone('Asia/Kolkata')

bot = telebot.TeleBot(BOT_TOKEN)

# --- TELEGRAM /status COMMAND ---
@bot.message_handler(commands=['status'])
def send_status(message):
    if str(message.chat.id) == CHAT_ID:
        curr_time = datetime.now(IST).strftime("%I:%M:%S %p")
        text = (
            f"✅ **Eufy Recorder Status**\n\n"
            f"🕒 Time: {curr_time}\n"
            f"📡 Port: 8000 (Active)\n"
            f"🤖 Anti-Sleep: Enabled\n"
            f"🎥 Monitoring: Running..."
        )
        bot.reply_to(message, text, parse_mode='Markdown')

def start_bot():
    """Bot listener ko alag thread mein chalane ke liye"""
    bot.infinity_polling()

def send_video_to_telegram(video_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    caption = f"📹 **Motion Detected!**\n⏰ {datetime.now(IST).strftime('%I:%M:%S %p')}"
    try:
        with open(video_path, 'rb') as f:
            requests.post(url, data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'video': f})
        if os.path.exists(video_path): os.remove(video_path)
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

# Bot listener shuru karein
threading.Thread(target=start_bot, daemon=True).start()

print("🚀 System Active on Port 8000 with /status command support.")

while True:
    now = datetime.now(IST)
    
    # Internal Heartbeat for Koyeb
    try:
        requests.get(KOYEB_URL, timeout=2)
    except:
        pass

    if 0 <= now.hour < 24:
        filename = f"rec_{int(time.time())}.mp4"
        
        # High Quality Encoding for Telegram Compatibility
        ffmpeg_cmd = (
            f"ffmpeg -y -loglevel error -i {KOYEB_URL}/live_stream_link "
            f"-t 30 -c:v libx264 -preset ultrafast -crf 28 -c:a aac {filename}"
        )
        
        status = os.system(ffmpeg_cmd)
        
        if status == 0 and os.path.exists(filename):
            print(f"✅ Video Captured!")
            send_video_to_telegram(filename)
            time.sleep(300) # 5 min gap after success
        else:
            print(f"🔍 Monitoring... {now.strftime('%H:%M:%S')}")
            time.sleep(60)
    else:
        time.sleep(60)
