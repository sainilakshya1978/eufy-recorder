import telebot, os, websocket, json, threading, time, socket
from flask import Flask
from datetime import datetime

# --- Config ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
WS_URL = "ws://127.0.0.1:8000"

# Telegram Bot Setup
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Helper Functions ---
def send_msg(text):
    try:
        print(f"📤 TG: {text}")
        bot.send_message(CHAT_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"⚠️ TG Fail: {e}")

# --- Flask Health Check ---
@app.route('/')
def health():
    return "Running", 200

# --- Motion Alert ---
def send_alert(sn):
    # Text Alert
    send_msg(f"🚨 **MOTION DETECTED!**\n📹 Cam: `{sn}`\n⏰ {datetime.now().strftime('%H:%M:%S')}")
    try:
        time.sleep(2)
        bot.send_photo(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image", caption="📸 Snap")
        time.sleep(15)
        bot.send_video(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_video", caption="🎥 Clip")
    except: pass

# --- WebSocket Logic ---
def on_message(ws, message):
    try:
        data = json.loads(message)
        
        # Connection Success Message
        if data.get("type") == "result" and "devices" in data.get("result", {}):
            devs = data["result"]["devices"]
            names = ", ".join([d.get("name", "Unk") for d in devs])
            send_msg(f"✅ **Eufy Bridge Connected!**\n📸 Cameras: `{names}`")

        # Motion Logic
        if data.get("type") == "event" and "event" in data:
            evt = data["event"]
            if "motion" in evt.get("name", "").lower():
                sn = evt.get("serialNumber")
                if sn: threading.Thread(target=send_alert, args=(sn,)).start()
    except Exception as e:
        print(f"JSON Error: {e}")

def start_ws():
    # Pehle check karein ki port 8000 khula hai ya nahi
    print("⏳ Waiting for Eufy Driver (Port 8000)...")
    time.sleep(10)
    
    while True:
        try:
            # Socket test
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 8000))
            sock.close()
            
            if result == 0:
                print("🔌 Port 8000 Open! Connecting WS...")
                ws = websocket.WebSocketApp(WS_URL,
                    on_open=lambda ws: ws.send(json.dumps({"command": "device.get_devices", "messageId": "init"})),
                    on_message=on_message)
                ws.run_forever()
            else:
                print("❌ Port 8000 closed. Driver starting...")
                time.sleep(5)
        except Exception as e:
            print(f"WS Error: {e}")
            time.sleep(10)

# --- Main Thread ---
if __name__ == "__main__":
    # 1. Startup Msg
    send_msg("🚀 **New Instance Started!**\n⏳ Waiting 45s for old container to die (Fixing 409 Error)...")

    # 2. Threads start karein (Ye background me chalenge)
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
    threading.Thread(target=start_ws, daemon=True).start()

    # 3. CRITICAL: 45 Second Wait for Old Container to Die
    time.sleep(45)

    # 4. Ab Polling shuru karein
    print("🤖 Starting Telegram Polling...")
    send_msg("🟢 **Bot Active!** Monitoring Motion now.")
    
    try:
        bot.delete_webhook(drop_pending_updates=True)
        # Interval badhane se CPU load kam hoga aur conflict kam honge
        bot.polling(non_stop=True, interval=2, timeout=20)
    except Exception as e:
        print(f"Polling Crash: {e}")
        time.sleep(10)
