import telebot, os, websocket, json, threading, time, socket
from flask import Flask
from datetime import datetime

# --- Config ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
WS_URL = "ws://127.0.0.1:8000"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Helper ---
def send_msg(text):
    try:
        print(f"📤 TG: {text}")
        bot.send_message(CHAT_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"⚠️ TG Fail: {e}")

@app.route('/')
def health(): return "Running", 200

# --- Alert Logic ---
def send_alert(sn):
    send_msg(f"🚨 **MOTION DETECTED!**\n📹 Cam: `{sn}`\n⏰ {datetime.now().strftime('%H:%M:%S')}")
    try:
        time.sleep(2)
        bot.send_photo(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image", caption="📸 Snap")
        time.sleep(15)
        bot.send_video(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_video", caption="🎥 Clip")
    except: pass

# --- WebSocket ---
def on_message(ws, message):
    try:
        data = json.loads(message)
        
        # Connection Success
        if data.get("type") == "result" and "devices" in data.get("result", {}):
            devs = data["result"]["devices"]
            names = ", ".join([d.get("name", "Unknown") for d in devs])
            send_msg(f"✅ **Connected!**\n📹 Cameras: `{names}`")

        # Motion Event
        if data.get("type") == "event" and "event" in data:
            evt = data["event"]
            if "motion" in evt.get("name", "").lower():
                sn = evt.get("serialNumber")
                if sn: threading.Thread(target=send_alert, args=(sn,)).start()
    except Exception as e:
        print(f"JSON Error: {e}")

def start_ws():
    print("⏳ Waiting for Port 8000...")
    time.sleep(10)
    while True:
        try:
            # Check if port is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 8000))
            sock.close()
            
            if result == 0:
                ws = websocket.WebSocketApp(WS_URL,
                    on_open=lambda ws: ws.send(json.dumps({"command": "device.get_devices", "messageId": "init"})),
                    on_message=on_message)
                ws.run_forever()
            else:
                print("❌ Driver not ready yet...")
                time.sleep(5)
        except:
            time.sleep(10)

if __name__ == "__main__":
    send_msg("🚀 **Instance Started!**\nWaiting 45s for conflict resolution...")
    
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
    threading.Thread(target=start_ws, daemon=True).start()

    time.sleep(45) # 409 Conflict Fix
    
    print("🤖 Polling Started...")
    try:
        bot.delete_webhook(drop_pending_updates=True)
        bot.polling(non_stop=True, interval=2)
    except Exception as e:
        print(f"Polling Error: {e}")
