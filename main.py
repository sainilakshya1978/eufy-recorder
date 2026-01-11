import telebot, os, websocket, json, threading, time
from flask import Flask

# 1. Config
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
CHAT_ID = os.getenv('CHAT_ID')
app = Flask(__name__)

# 2. Minimal Flask (Koyeb Health Check ke liye)
@app.route('/')
def health(): return "Bot is Alive", 200

def run_flask():
    # Health check port 5000 par hi chalega
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# 3. Motion Media Logic
def send_media(sn):
    try:
        # Photo
        bot.send_photo(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image", caption="🚨 Motion!")
        time.sleep(15)
        # Video
        bot.send_video(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_video", caption="🎥 Clip")
    except Exception as e: print(f"❌ Error: {e}")

# 4. WebSocket Connection
def on_msg(ws, msg):
    data = json.loads(msg)
    if "motion" in str(data).lower():
        sn = data.get("metadata", {}).get("serial_number")
        if sn: threading.Thread(target=send_media, args=(sn,)).start()

def start_ws():
    while True:
        try:
            ws = websocket.WebSocketApp("ws://127.0.0.1:8000", on_message=on_msg)
            ws.run_forever()
        except: time.sleep(10)

if __name__ == "__main__":
    # Sabse pehle Flask start karo taaki Koyeb 'Healthy' dikhaye
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("⏳ Waiting 60s for Eufy Login...")
    time.sleep(60)
    
    # Phir Bot start karo
    threading.Thread(target=start_ws, daemon=True).start()
    bot.polling(none_stop=True)
