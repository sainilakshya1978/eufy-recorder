import telebot, os, websocket, json, threading, time
from flask import Flask

bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
CHAT_ID = os.getenv('CHAT_ID')
app = Flask(__name__)

@app.route('/')
def home(): return "OK", 200

def run_flask(): app.run(host='0.0.0.0', port=5000)

def on_message(ws, message):
    data = json.loads(message)
    if "motion" in str(data).lower():
        sn = data.get("metadata", {}).get("serial_number")
        if sn:
            bot.send_photo(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image", caption="🚨 Motion!")

def start_ws():
    while True:
        try:
            ws = websocket.WebSocketApp("ws://127.0.0.1:8000", on_message=on_message)
            ws.run_forever()
        except: time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("⏳ Giving Driver 60s to login...")
    time.sleep(60) # Authentication ke liye buffer time
    threading.Thread(target=start_ws, daemon=True).start()
    bot.polling(none_stop=True)
