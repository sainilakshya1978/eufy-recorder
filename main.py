import telebot, os, websocket, json, threading, time
from flask import Flask
from datetime import datetime

# --- Config ---
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
CHAT_ID = os.getenv('CHAT_ID')
app = Flask(__name__)

TESTING_MODE = True 
START_H, END_H = 0, 5 

@app.route('/')
def health(): return "Healthy", 200

@bot.message_handler(commands=['status'])
def status(message):
    bot.reply_to(message, f"✅ Bot Online\nMode: {'TEST' if TESTING_MODE else 'LIVE (12-5)'}")

def send_alert(sn):
    now = datetime.now().hour
    if TESTING_MODE or (START_H <= now < END_H):
        try:
            # CPU bachane ke liye image/video request ke beech gap
            bot.send_photo(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image", caption="🚨 Motion Detected!")
            time.sleep(10) 
            bot.send_video(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_video")
        except Exception as e: print(f"❌ Media Error: {e}")

def on_msg(ws, msg):
    data = json.loads(msg)
    # Check for motion events accurately
    if data.get("type") == "event" and "motion" in str(data).lower():
        sn = data.get("event", {}).get("serialNumber")
        if sn: threading.Thread(target=send_alert, args=(sn,)).start()

def ws_loop():
    print("⏳ Waiting 100s for Driver to stabilize...")
    time.sleep(100) # Thoda extra time for CPU to cool down
    while True:
        try:
            ws = websocket.WebSocketApp("ws://127.0.0.1:8000", on_message=on_msg)
            ws.run_forever()
        except: 
            time.sleep(20)

def start_polling():
    # 409 Error fix: Wait for old instance to die and clear webhook
    time.sleep(30)
    bot.remove_webhook()
    print("🚀 Starting Telegram Polling...")
    bot.polling(none_stop=True, interval=3) # Interval adds small delay to save CPU

if __name__ == "__main__":
    # 1. Flask Health Check (Koyeb helps keeping it alive)
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()
    
    # 2. WebSocket Thread
    threading.Thread(target=ws_loop, daemon=True).start()
    
    # 3. Bot Polling
    start_polling()
