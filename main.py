import telebot, os, websocket, json, threading, time, requests, subprocess
from flask import Flask
from datetime import datetime
import pytz

# --- Config ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
IST = pytz.timezone('Asia/Kolkata')
WS_URL = "ws://127.0.0.1:3000"
API_URL = "http://127.0.0.1:3000"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def health(): return "Ready for Test", 200

def trigger_live_test():
    sn = "T8W11P40240109D4" # Aapka Camera SN
    file_name = "test_2257.mp4"
    
    bot.send_message(CHAT_ID, "🚀 **CRITICAL TEST START (22:57):** Final attempt for Live Video...")

    try:
        # 1. Wake up stream
        requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream")
        time.sleep(8) # Extra wait for cloud handshake
        
        # 2. FFmpeg Capture (60 seconds)
        # Force overwrite (-y) and copy codec for speed
        cmd = f"ffmpeg -i {API_URL}/api/v1/devices/{sn}/live -t 60 -c copy -y {file_name}"
        subprocess.run(cmd, shell=True, timeout=100)
        
        # 3. Check and Send
        if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
            with open(file_name, 'rb') as video:
                bot.send_video(CHAT_ID, video, caption="🎯 **Test Successful!**\nLive View Captured: 22:57 - 22:58")
            os.remove(file_name)
        else:
            bot.send_message(CHAT_ID, "❌ **Test Failed:** No video data. Is the camera online?")

        requests.post(f"{API_URL}/api/v1/devices/{sn}/stop_livestream")
    except Exception as e:
        bot.send_message(CHAT_ID, f"⚠️ **System Error:** {str(e)}")

def check_time_loop():
    print("⏰ Monitoring time for 22:57...")
    while True:
        now = datetime.now(IST)
        # Exact 22:57:00 par trigger
        if now.hour == 22 and now.minute == 57:
            trigger_live_test()
            break 
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    threading.Thread(target=check_time_loop, daemon=True).start()
    bot.polling(none_stop=True)
