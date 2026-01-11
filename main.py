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

# 2. Web Server
@app.route('/')
def home():
    return "<h1>✅ Eufy Bot is Active and Monitoring!</h1>", 200

def run_flask():
    app.run(host='0.0.0.0', port=5000)

# 3. Motion Alert Logic
def handle_motion(device_sn):
    print(f"🔔 Motion detected for device: {device_sn}") # Logs mein dikhega
    try:
        # 127.0.0.1 use karein localhost ki jagah
        img_url = f"http://127.0.0.1:8000/api/v1/devices/{device_sn}/last_image"
        bot.send_photo(CHAT_ID, img_url, caption=f"🚨 Motion Detected!\nDevice: {device_sn}")
        
        time.sleep(5)
        video_url = f"http://127.0.0.1:8000/api/v1/devices/{device_sn}/last_video"
        bot.send_video(CHAT_ID, video_url, caption="🎥 Recorded Motion Clip")
    except Exception as e:
        print(f"❌ Media Error: {e}")

# 4. WebSocket (Connection fix)
def on_message(ws, message):
    data = json.loads(message)
    # Debug ke liye saare messages print karein
    print(f"📩 New Message from Eufy: {data.get('type')}") 
    
    if "event" in data and data["event"] == "device.event_added":
        if data["metadata"].get("event_type") == "motion":
            device_sn = data["metadata"]["serial_number"]
            handle_motion(device_sn)

def on_error(ws, error):
    print(f"❌ WebSocket Error: {error}")

def on_open(ws):
    print("✅ Connected to Eufy Security Server!")

def start_ws():
    # Yahan localhost ki jagah 127.0.0.1 try karein
    ws = websocket.WebSocketApp(
        "ws://127.0.0.1:8000", 
        on_message=on_message,
        on_error=on_error,
        on_open=on_open
    )
    ws.run_forever()

# 5. Telegram Status Command
@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, f"✅ System Status: Online\n🕒 Time: {time.strftime('%H:%M:%S')}\n📡 Monitoring: Active")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    # 5 second wait karein taaki background server start ho jaye
    time.sleep(5) 
    threading.Thread(target=start_ws, daemon=True).start()
    
    print("🚀 Bot is starting...")
    bot.delete_webhook(drop_pending_updates=True)
    bot.polling(none_stop=True)
