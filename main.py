import telebot, os, websocket, json, threading, time, requests
from flask import Flask
from datetime import datetime
import pytz

# --- Config ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
IST = pytz.timezone('Asia/Kolkata')
WS_URL = "ws://127.0.0.1:3000"
API_URL = "http://127.0.0.1:3000"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def health(): return "Healthy", 200

# --- Advanced Alert Engine ---
def process_full_alert(sn):
    now = datetime.now(IST).strftime('%H:%M:%S')
    
    # 1. PRIORITY 1: Instant Text
    bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED!**\n📹 Cam: `{sn}`\n⏰ Time: `{now} IST`", parse_mode="Markdown")
    
    # 2. PRIORITY 2: Image (Wait 3s for Cloud Update)
    try:
        time.sleep(3)
        img_res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=15)
        if img_res.status_code == 200:
            bot.send_photo(CHAT_ID, img_res.content, caption="📸 Instant Snapshot")
    except Exception as e:
        print(f"Image Error: {e}")

    # 3. PRIORITY 3: Video (Wait 20s for SD Card/Cloud Processing)
    # Background thread mein chalega taaki bot busy na ho
    def fetch_video():
        time.sleep(20) 
        try:
            vid_res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_video", timeout=30)
            if vid_res.status_code == 200:
                bot.send_video(CHAT_ID, vid_res.content, caption="🎥 Evidence Video (Recorded)")
        except Exception as e:
            print(f"Video Error: {e}")

    threading.Thread(target=fetch_video).start()

# --- WebSocket Listener ---
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "event":
        evt = data.get("event", {})
        # Sabhi types ke motion aur rings ko pakadne ke liye logic
        if any(x in evt.get("name", "").lower() for x in ["motion", "person", "pet", "ring"]):
            sn = evt.get("serialNumber")
            if sn:
                # Threading use ki hai taaki har alert independently chale
                threading.Thread(target=process_full_alert, args=(sn,)).start()

def on_open(ws):
    ws.send(json.dumps({"command": "start_listening", "messageId": "start"}))

def run_ws():
    while True:
        try:
            ws = websocket.WebSocketApp(WS_URL, on_open=on_open, on_message=on_message)
            ws.run_forever()
        except: pass
        time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    time.sleep(5)
    threading.Thread(target=run_ws, daemon=True).start()
    bot.polling(none_stop=True)
