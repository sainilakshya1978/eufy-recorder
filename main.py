import telebot, os, websocket, json, threading, time
from flask import Flask
from datetime import datetime

# --- Config ---
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
CHAT_ID = os.getenv('CHAT_ID')
app = Flask(__name__)

# Testing ke liye True rakhein, final ke liye False
TESTING_MODE = True 
START_H, END_H = 0, 5 # Raat 12 se Subah 5

@app.route('/')
def health(): return "Healthy", 200

@bot.message_handler(commands=['status'])
def status(message):
    bot.reply_to(message, f"✅ Bot Online\nMode: {'TEST' if TESTING_MODE else 'LIVE (12-5)'}")

def send_alert(sn):
    now = datetime.now().hour
    if TESTING_MODE or (START_H <= now < END_H):
        try:
            # Photo pehle bhejein
            bot.send_photo(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image", caption="🚨 Motion Raat 12-5!")
            time.sleep(20) # Video processing time
            bot.send_video(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_video")
        except Exception as e: print(f"❌ Media Error: {e}")

def on_msg(ws, msg):
    data = json.loads(msg)
    if "motion" in str(data).lower():
        sn = data.get("metadata", {}).get("serial_number")
        if sn: threading.Thread(target=send_alert, args=(sn,)).start()

def ws_loop():
    # CPU usage kam karne ke liye 90s wait
    print("⏳ Waiting 90s for Driver Login...")
    time.sleep(90) 
    while True:
        try:
            ws = websocket.WebSocketApp("ws://127.0.0.1:8000", on_message=on_msg)
            ws.run_forever()
        except: time.sleep(15)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    threading.Thread(target=ws_loop, daemon=True).start()
    bot.polling(none_stop=True)
