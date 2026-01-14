import telebot, os, websocket, json, threading, time, requests, subprocess
from flask import Flask
from datetime import datetime
import pytz

# --- Config ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://127.0.0.1:3000"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def health(): return "Ready for 23:07 Test", 200

def trigger_live_test():
    sn = "T8W11P40240109D4"
    file_name = "test_2307.mp4"
    
    bot.send_message(CHAT_ID, "🚀 **FINAL TEST START (23:07):** Capturing Live Video...")

    try:
        # 1. Start Stream
        requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream")
        time.sleep(12) # Handshake buffer
        
        # 2. FFmpeg Capture (60s)
        cmd = f"ffmpeg -i {API_URL}/api/v1/devices/{sn}/live -t 60 -c copy -y {file_name}"
        subprocess.run(cmd, shell=True, timeout=120)
        
        if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
            with open(file_name, 'rb') as video:
                bot.send_video(CHAT_ID, video, caption="✅ **SUCCESS!** Live: 23:07 - 23:08")
            os.remove(file_name)
        else:
            bot.send_message(CHAT_ID, "❌ **Capture Failed:** Driver active but no camera data.")

        requests.post(f"{API_URL}/api/v1/devices/{sn}/stop_livestream")
    except Exception as e:
        bot.send_message(CHAT_ID, f"⚠️ **Critical Error:** {str(e)}")

def check_time_loop():
    while True:
        now = datetime.now(IST)
        if now.hour == 23 and now.minute == 7:
            trigger_live_test()
            break 
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    threading.Thread(target=check_time_loop, daemon=True).start()
    bot.polling(none_stop=True)
