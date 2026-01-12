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
        print(f"⚠️ TG Error: {e}")

@app.route('/')
def health(): return "Healthy", 200

# --- Motion Alert Logic ---
def send_alert(sn):
    timestamp = datetime.now().strftime('%H:%M:%S')
    send_msg(f"🚨 **MOTION DETECTED!**\n📹 Cam: `{sn}`\n⏰ Time: `{timestamp}`")
    
    try:
        # Photo
        time.sleep(2)
        bot.send_photo(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image", caption="📸 Snapshot")
        # Video
        time.sleep(15)
        bot.send_video(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_video", caption="🎥 Clip")
    except Exception as e:
        print(f"⚠️ Media Error: {e}")

# --- WebSocket Listener ---
def on_message(ws, message):
    try:
        data = json.loads(message)
        
        # Connection Success Check
        if data.get("type") == "result" and "devices" in data.get("result", {}):
            count = len(data['result']['devices'])
            send_msg(f"✅ **Eufy Connected!**\nFound {count} Cameras.")

        # Motion Event Check
        if data.get("type") == "event" and "event" in data:
            evt = data["event"]
            if "motion" in evt.get("name", "").lower():
                sn = evt.get("serialNumber")
                if sn: threading.Thread(target=send_alert, args=(sn,)).start()
    except: pass

def start_ws():
    print("⏳ Python: Waiting for Driver (20s)...")
    time.sleep(20) # Startup delay
    
    while True:
        try:
            # Check if Port 8000 is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 8000))
            sock.close()
            
            if result == 0:
                print("🔌 Connecting WebSocket...")
                ws = websocket.WebSocketApp(WS_URL,
                    on_open=lambda ws: ws.send(json.dumps({"command": "device.get_devices", "messageId": "init"})),
                    on_message=on_message)
                ws.run_forever()
            else:
                print(".", end="", flush=True) # Waiting indicator
                time.sleep(5)
        except Exception as e:
            print(f"WS Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    send_msg("🚀 **Bot Restarting on Koyeb!**\nInitializing Systems...")
    
    # Start Background Threads
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
    threading.Thread(target=start_ws, daemon=True).start()
    
    # 409 Conflict Fix (Wait for old container to stop)
    time.sleep(40)
    
    print("🤖 Telegram Polling Started...")
    try:
        bot.delete_webhook(drop_pending_updates=True)
        bot.polling(non_stop=True, interval=5)
    except Exception as e:
        print(f"Polling Error: {e}")
