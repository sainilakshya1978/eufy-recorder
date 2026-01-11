import telebot, os, websocket, json, threading, time
from flask import Flask
from datetime import datetime

# --- Configuration ---
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
CHAT_ID = os.getenv('CHAT_ID')
app = Flask(__name__)

# TESTING MODE: True matlab abhi alerts aayenge. 
# 12-5 fix karne ke liye ise False kar dena baad mein.
TESTING_MODE = True 
START_H, END_H = 12, 17 

@app.route('/')
def health(): return "System Online", 200

# --- Telegram Status ---
@bot.message_handler(commands=['status'])
def status(message):
    now = datetime.now().hour
    msg = f"✅ Bot Active!\nWindow: 12PM-5PM\nCurrent Hour: {now}\nMode: {'TESTING' if TESTING_MODE else 'LIVE'}"
    bot.reply_to(message, msg)

# --- Media Logic ---
def send_alert(sn):
    now = datetime.now().hour
    # Agar Testing ON hai YA time 12-5 ke beech hai
    if TESTING_MODE or (START_H <= now < END_H):
        try:
            print(f"🚨 Sending Alert for {sn}")
            # Photo
            bot.send_photo(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image", caption=f"🚨 Motion Detected!")
            # Video Buffer
            time.sleep(20) 
            # Video
            bot.send_video(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_video", caption="🎥 Clip")
        except Exception as e: print(f"❌ Error: {e}")
    else:
        print(f"😴 Outside window ({now}:00), ignoring.")

# --- WebSocket ---
def on_msg(ws, msg):
    data = json.loads(msg)
    if "motion" in str(data).lower():
        sn = data.get("metadata", {}).get("serial_number")
        if sn: threading.Thread(target=send_alert, args=(sn,)).start()

def ws_loop():
    print("⏳ Waiting 60s for Driver...")
    time.sleep(60)
    while True:
        try:
            ws = websocket.WebSocketApp("ws://127.0.0.1:8000", on_message=on_msg)
            ws.run_forever()
        except: time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    threading.Thread(target=ws_loop, daemon=True).start()
    print("🤖 Bot Started...")
    bot.polling(none_stop=True)
    
