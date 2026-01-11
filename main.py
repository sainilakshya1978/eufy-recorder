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

# 2. Web Server (White screen hatane aur Cron-job ko "Success" dene ke liye)
@app.route('/')
def home():
    return "<h1>✅ Eufy Bot is Active and Monitoring!</h1>", 200

def run_flask():
    # Port 8000 par Flask chalao
    app.run(host='0.0.0.0', port=8000)

# 3. Motion Alert Logic (Photo + Video)
def handle_motion(device_sn):
    try:
        # A. Photo Alert
        img_url = f"http://localhost:8000/api/v1/devices/{device_sn}/last_image"
        bot.send_photo(CHAT_ID, img_url, caption="🚨 Motion Detected! (Live Photo)")
        
        # B. Video Clip (5 sec wait ke baad)
        time.sleep(5)
        video_url = f"http://localhost:8000/api/v1/devices/{device_sn}/last_video"
        bot.send_video(CHAT_ID, video_url, caption="🎥 Recorded Motion Clip")
    except Exception as e:
        print(f"Media Error: {e}")

# 4. WebSocket (Asli monitoring start karne ke liye)
def on_message(ws, message):
    data = json.loads(message)
    if "event" in data and data["event"] == "device.event_added":
        if data["metadata"].get("event_type") == "motion":
            device_sn = data["metadata"]["serial_number"]
            handle_motion(device_sn)

def start_ws():
    # WebSocket port 8000 se jura rahega
    ws = websocket.WebSocketApp("ws://localhost:8000", on_message=on_message)
    ws.run_forever()

# 5. Telegram Status Command
@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, f"✅ System Status: Online\n🕒 Time: {time.strftime('%H:%M:%S')}\n📡 Monitoring: Active")

if __name__ == "__main__":
    # Background threads start karein
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=start_ws, daemon=True).start()
    print("🚀 Monitoring and Web Server Started...")
    # Isse purane saare conflict khatam ho jayenge
    bot.delete_webhook(drop_pending_updates=True)
    time.sleep(1)
    bot.polling(none_stop=True)
