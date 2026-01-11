import telebot
import os
import websocket
import json
import threading
import time
import socket
from flask import Flask

# 1. Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 2. Minimal Flask for Koyeb Health Check
@app.route('/')
def home():
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# 3. Motion Logic
def handle_motion(data):
    try:
        device_sn = data.get("metadata", {}).get("serial_number")
        if device_sn:
            img_url = f"http://127.0.0.1:8000/api/v1/devices/{device_sn}/last_image"
            bot.send_photo(CHAT_ID, img_url, caption="🚨 Motion Detected!")
    except Exception as e:
        print(f"❌ Alert Error: {e}")

# 4. WebSocket (Driver Connection)
def on_message(ws, message):
    data = json.loads(message)
    if "motion" in str(data).lower():
        handle_motion(data)

def start_ws():
    while True:
        try:
            ws = websocket.WebSocketApp("ws://127.0.0.1:8000", on_message=on_message)
            ws.run_forever()
        except:
            time.sleep(10)

if __name__ == "__main__":
    # Sabse pehle Flask (Health Check pass karne ke liye)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Driver ko login hone ka full time do (RAM release hone do)
    print("⏳ Waiting for Eufy Driver to breathe (60s)...")
    time.sleep(60)
    
    # Bot start
    threading.Thread(target=start_ws, daemon=True).start()
    print("🤖 Bot is active...")
    bot.polling(none_stop=True)
