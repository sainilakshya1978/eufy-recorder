import telebot
import requests
import time
import os
import websocket
import json
import threading

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 
bot = telebot.TeleBot(BOT_TOKEN)

# 1. Keep Alive Heartbeat
def keep_alive():
    while True:
        try:
            requests.get("http://localhost:8000/", timeout=5)
        except:
            pass
        time.sleep(45)

# 2. Motion Event Handler (Mobile App jaisa experience)
def handle_motion(data):
    try:
        device_sn = data['metadata']['serial_number']
        
        # A. Pehle Photo bheje (Jaisa mobile notification mein dikhta hai)
        # Bridge API se latest thumbnail fetch karna
        img_url = f"http://localhost:8000/api/v1/devices/{device_sn}/last_image"
        bot.send_photo(CHAT_ID, img_url, caption="📸 Eufy Alert: Motion Detected!")

        # B. Thoda ruk kar Video bheje (Taaki bridge clip save karle)
        time.sleep(5) 
        video_url = f"http://localhost:8000/api/v1/devices/{device_sn}/last_video"
        bot.send_video(CHAT_ID, video_url, caption="🎥 Motion Video Clip")
        
    except Exception as e:
        bot.send_message(CHAT_ID, f"⚠️ Alert received but media failed: {str(e)}")

# 3. WebSocket Real Monitoring Start
def on_message(ws, message):
    data = json.loads(message)
    # Eufy bridge motion signal check
    if "event" in data and data["event"] == "device.event_added":
        if data["metadata"].get("event_type") == "motion":
            handle_motion(data)

def start_monitoring():
    # Bridge Port 8000 connection
    ws = websocket.WebSocketApp("ws://localhost:8000", on_message=on_message)
    ws.run_forever()

if __name__ == "__main__":
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=start_monitoring, daemon=True).start()
    bot.polling(none_stop=True)
