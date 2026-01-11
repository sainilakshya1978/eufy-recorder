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

# 2. Web Server (Koyeb Health Check ke liye port 5000 use karega)
@app.route('/')
def home():
    return "<h1>✅ Eufy Bot is Active!</h1>", 200

def run_flask():
    print("🌐 Starting Flask on port 5000...")
    app.run(host='0.0.0.0', port=5000)

# 3. Motion Alert Logic
def handle_motion(device_sn):
    print(f"🚨 MOTION DETECTED: {device_sn}")
    try:
        # Eufy server port 3000 par hota hai
        img_url = f"http://127.0.0.1:3000/api/v1/devices/{device_sn}/last_image"
        bot.send_photo(CHAT_ID, img_url, caption="🚨 Motion Detected!")
        
        time.sleep(5)
        video_url = f"http://127.0.0.1:3000/api/v1/devices/{device_sn}/last_video"
        bot.send_video(CHAT_ID, video_url, caption="🎥 Video Clip")
    except Exception as e:
        print(f"❌ Media Error: {e}")

# 4. WebSocket Connection
def on_message(ws, message):
    data = json.loads(message)
    # Ye line logs mein batayegi ki camera se data aa raha hai
    print(f"📩 Eufy Event: {data.get('type')}")
    
    if data.get("type") == "event" and data.get("event") == "device.event_added":
        if data["metadata"].get("event_type") == "motion":
            handle_motion(data["metadata"]["serial_number"])

def on_open(ws):
    print("✅ SUCCESS: Connected to Eufy Camera Server!")

def on_error(ws, error):
    print(f"❌ Connection Error: {error}")

def start_ws():
    # Hum 3000 port try kar rahe hain kyunki 8000 Flask ke paas hai
    ws = websocket.WebSocketApp(
        "ws://127.0.0.1:3000", 
        on_message=on_message, 
        on_open=on_open, 
        on_error=on_error
    )
    ws.run_forever()

# 5. Telegram Status
@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, "✅ Bot is Online and Watching!")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(10) # Server chalu hone ka wait
    threading.Thread(target=start_ws, daemon=True).start()
    
    bot.delete_webhook(drop_pending_updates=True)
    bot.polling(none_stop=True)
