import telebot
import requests
import time
import os
import websocket
import json
import threading
import socket
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
        
        # Video ke liye thoda wait karein (Internet slow ho to 10s ka 15s kar sakte hain)
        time.sleep(10) 
        video_url = f"http://127.0.0.1:8000/api/v1/devices/{device_sn}/last_video"
        bot.send_video(CHAT_ID, video_url, caption="🎥 Video Clip")
    except Exception as e:
        print(f"❌ Media Error: {e}")

# 4. WebSocket Connection
def on_message(ws, message):
    data = json.loads(message)
    # Debugging ke liye message type print karein
    if data.get("type") != "keep-alive":
        print(f"📩 Event: {data.get('type')}")
        
    if data.get("type") == "event" and "motion" in str(data).lower():
        device_sn = data.get("metadata", {}).get("serial_number")
        if device_sn:
            handle_motion(device_sn)

def on_open(ws):
    print("✅ SUCCESS: Connected to Eufy Camera Server on Port 8000!")

def on_error(ws, error):
    print(f"⚠️ WS Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("⚠️ Connection Closed. Retrying...")

def start_ws():
    while True:
        try:
            # 127.0.0.1 hi use karein
            ws = websocket.WebSocketApp(
                "ws://127.0.0.1:8000", 
                on_message=on_message, 
                on_open=on_open, 
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever()
        except Exception as e:
            print(f"❌ WS Exception: {e}")
        
        print("⏳ Reconnecting in 5 seconds...")
        time.sleep(5)

# 5. Smart Server Check (New Feature)
def check_eufy_server():
    print("🔍 Checking if Eufy Driver is ready on Port 8000...")
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 8000))
            sock.close()
            if result == 0:
                print("✅ Eufy Driver is UP! Starting Bot...")
                break
            else:
                print("⏳ Driver starting... waiting 5s...")
                time.sleep(5)
        except:
            time.sleep(5)

# 6. Telegram Status
@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, "✅ Bot Status: Online & Monitoring")

if __name__ == "__main__":
    # Flask start
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Pehle check karo ki server ready hai ya nahi
    threading.Thread(target=check_eufy_server).start()
    
    # Phir thodi der baad WebSocket try karo
    time.sleep(10)
    threading.Thread(target=start_ws, daemon=True).start()
    
    print("🤖 Telegram Bot Polling Started...")
    bot.delete_webhook(drop_pending_updates=True)
    bot.polling(none_stop=True, timeout=60)
