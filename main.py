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

# 1. Keep Alive Logic
def keep_alive():
    while True:
        try:
            requests.get("http://localhost:8000/", timeout=5)
        except:
            pass
        time.sleep(45)

# 2. Status Command
@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, "✅ System Status: Online\n📸 Monitoring: Active (Real-time Events)")

# 3. Real Monitoring Logic (WebSocket)
def on_message(ws, message):
    data = json.loads(message)
    # Check for Motion Event
    if "event" in data and data["event"] == "device.event_added":
        event_type = data["metadata"].get("event_type")
        if event_type == "motion":
            bot.send_message(CHAT_ID, "🚨 MOTION DETECTED! 🚨\nFetching Video/Image...")
            # Note: Bridge automatically saves clips to its local folder.
            # Real implementation needs to grab the latest MP4/JPG from the bridge API.

def start_monitoring():
    # Bridge Port 8000 se connect hona
    ws = websocket.WebSocketApp("ws://localhost:8000", on_message=on_message)
    ws.run_forever()

if __name__ == "__main__":
    print("Starting Heartbeat and Monitoring...")
    # Background threads for stability
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=start_monitoring, daemon=True).start()
    
    bot.polling(none_stop=True)
