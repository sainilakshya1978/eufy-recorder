import requests
import time
import os
import telebot
from datetime import datetime
import pytz
import threading

# --- CONFIG ---
KOYEB_URL = "http://localhost:8000" 
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = pytz.timezone('Asia/Kolkata')

bot = telebot.TeleBot(BOT_TOKEN)

# Telegram /status handler
@bot.message_handler(commands=['status'])
def send_status(message):
    if str(message.chat.id) == CHAT_ID:
        curr_time = datetime.now(IST).strftime("%I:%M:%S %p")
        text = f"✅ **System Status**\n\n🕒 Time: {curr_time}\n📡 Server: Online (Port 8000)\n🎥 Monitoring: Active"
        bot.reply_to(message, text, parse_mode='Markdown')

def start_bot():
    bot.infinity_polling()

# Bot ko background thread mein start karein
threading.Thread(target=start_bot, daemon=True).start()

print("🚀 Monitoring Active with /status support...")

while True:
    now = datetime.now(IST)
    # Anti-sleep internal ping
    try: requests.get(KOYEB_URL, timeout=2)
    except: pass

    filename = f"rec_{int(time.time())}.mp4"
    # High compatibility encoding
    ffmpeg_cmd = (f"ffmpeg -y -loglevel error -i {KOYEB_URL}/live_stream_link "
                  f"-t 30 -c:v libx264 -preset ultrafast -crf 28 -c:a aac {filename}")
    
    if os.system(ffmpeg_cmd) == 0 and os.path.exists(filename):
        with open(filename, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo", 
                          data={'chat_id': CHAT_ID, 'caption': f'📹 Motion: {now.strftime("%I:%M %p")}'}, 
                          files={'video': f})
        os.remove(filename)
        time.sleep(300)
    else:
        time.sleep(60)
