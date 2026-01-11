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

# 2. Web Server (Koyeb Health Check - Port 5000)
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
        # Port 8000 Driver ke liye
        img_url = f"http://127.0.0.1:8000/api/v1/devices/{device_sn}/last_image"
        bot.send_photo(CHAT_ID, img_url, caption=f"🚨 Motion Detected!\nDevice: {device_sn}")
        
        time.sleep(10) # Video record hone ka wait
        video_url = f"http://127.0.0.1:8000/api/v1/devices/{device_sn}/last_video"
        bot.send_video(CHAT_ID, video_url, caption="🎥 Video Clip")
    except Exception as e:
        print(f"❌ Media Error: {e}")

# 4. WebSocket Connection
def on_message(ws, message):
    data = json.loads(message)
    print(f"📩 Message: {data.get('type')}")
    if data.get("type") == "event" and "motion" in str(data).lower():
        device_sn = data.get("metadata", {}).get("serial_number")
        if device_sn:
            handle_motion(device_sn)

def on_open(ws):
    print("✅ SUCCESS: Connected to Eufy Camera Server!")

def on_error(ws, error):
    print(f"❌ Connection Error: {error}")

def start_ws():
    # Loop taaki agar connection tute toh wapas jud jaye
    while True:
        try:
            ws = websocket.WebSocketApp(
                "ws://127.0.0.1:8000", 
                on_message=on_message, 
                on_open=on_open, 
                on_error=on_error
            )
            ws.run_forever()
        except:
            pass
        time.sleep(5)

# 5. Telegram Status
@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, "✅ Bot Status: Online & Monitoring")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(20) # Docker startup grace period
    threading.Thread(target=start_ws, daemon=True).start()
    
    print("🤖 Bot is starting...")
    bot.delete_webhook(drop_pending_updates=True)
    bot.polling(none_stop=True, timeout=60)
