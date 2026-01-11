import telebot
import requests
import time
import os
import websocket
import json
import threading
from flask import Flask

# 1. Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 2. Web Server (Taaki browser aur Cron-job ko response mile)
@app.route('/')
def home():
    return "✅ Bot is Active and Monitoring!", 200

def run_flask():
    app.run(host='0.0.0.0', port=8000)

# 3. Motion Media Fetcher (Asli Photo aur Video)
def send_motion_media(device_sn):
    try:
        # Latest image fetch karke Telegram par bhejna
        img_url = f"http://localhost:8000/api/v1/devices/{device_sn}/last_image"
        bot.send_photo(CHAT_ID, img_url, caption="🚨 Motion Detected! (Live Photo)")
        
        # 5 sec rukna taaki video file ready ho jaye
        time.sleep(5)
        video_url = f"http://localhost:8000/api/v1/devices/{device_sn}/last_video"
        bot.send_video(CHAT_ID, video_url, caption="🎥 Recorded Clip")
    except Exception as e:
        print(f"Media Error: {e}")

# 4. WebSocket Listener (Real-time monitoring start)
def on_message(ws, message):
    data = json.loads(message)
    if "event" in data and data["event"] == "device.event_added":
        if data["metadata"].get("event_type") == "motion":
            device_sn = data["metadata"]["serial_number"]
            send_motion_media(device_sn)

def start_ws():
    ws = websocket.WebSocketApp("ws://localhost:8000", on_message=on_message)
    ws.run_forever()

# 5. Status Command
@bot.message_handler(commands=['status'])
def status(message):
    bot.reply_to(message, f"✅ System Online\n🕒 {time.strftime('%H:%M:%S')}\n📡 Monitoring Active")

if __name__ == "__main__":
    # Sabhi components ko threads mein chalana
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=start_ws, daemon=True).start()
    print("🚀 All systems started...")
    bot.polling(none_stop=True)
