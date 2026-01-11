import telebot, os, websocket, json, threading, time
from flask import Flask

# 1. Config
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
CHAT_ID = os.getenv('CHAT_ID')
app = Flask(__name__)

@app.route('/')
def health(): return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# 2. Telegram Status Handler (Turant kaam karega)
@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, "✅ Bot is Online!\n⏳ Eufy Bridge connecting in background...")

# 3. Motion Logic
def send_media(sn):
    try:
        bot.send_photo(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image", caption="🚨 Motion!")
        time.sleep(15)
        bot.send_video(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_video", caption="🎥 Clip")
    except Exception as e: print(f"❌ Media Error: {e}")

# 4. WebSocket (Bridge Connection)
def on_msg(ws, msg):
    data = json.loads(msg)
    if "motion" in str(data).lower():
        sn = data.get("metadata", {}).get("serial_number")
        if sn: threading.Thread(target=send_media, args=(sn,)).start()

def start_ws_loop():
    print("⏳ Waiting 60s for Eufy Driver to finish login...")
    time.sleep(60) # Sirf ye thread wait karega, bot nahi
    while True:
        try:
            print("🔗 Connecting to Eufy Bridge (Port 8000)...")
            ws = websocket.WebSocketApp("ws://127.0.0.1:8000", 
                                        on_message=on_msg,
                                        on_open=lambda ws: print("✅ SUCCESS: Connected to Camera!"))
            ws.run_forever()
        except: time.sleep(10)

if __name__ == "__main__":
    # Flask start (Koyeb Health Check)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # WebSocket Bridge (Background thread)
    threading.Thread(target=start_ws_loop, daemon=True).start()
    
    # Telegram Bot Polling (Main thread - Turant start hoga)
    print("🤖 Telegram Bot Polling Started...")
    bot.remove_webhook()
    bot.polling(none_stop=True)
