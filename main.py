import telebot, os, websocket, json, threading, time
from flask import Flask
from datetime import datetime

# --- Config ---
# Environment variables load karein
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# Connection Settings
WS_URL = "ws://127.0.0.1:8000"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Helper: Send Message to Telegram ---
def send_msg(text):
    try:
        print(f"📤 TG Log: {text}")
        bot.send_message(CHAT_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

# --- Flask Health Check ---
@app.route('/')
def health():
    return "Online", 200

# --- Alert Logic ---
def send_alert(sn):
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    # Step 1: Text Alert (Instant)
    send_msg(f"🚨 **MOTION DETECTED!**\n📹 Camera: `{sn}`\n⏰ Time: `{timestamp}`")
    
    try:
        # Step 2: Image
        # Thoda wait karein taaki camera image save kar le
        time.sleep(2) 
        img_url = f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image"
        bot.send_photo(CHAT_ID, img_url, caption="📸 Snapshot")
        
        # Step 3: Video
        # Video process hone mein time lagta hai (15-20s)
        time.sleep(15)
        vid_url = f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_video"
        bot.send_video(CHAT_ID, vid_url, caption="🎥 Event Video")
        
    except Exception as e:
        send_msg(f"⚠️ Media Error: `{e}`\n(Text alert sent successfully)")

# --- WebSocket Listener ---
def on_message(ws, message):
    try:
        data = json.loads(message)

        # A. Startup: Check Devices
        if data.get("type") == "result" and "devices" in data.get("result", {}):
            devices = data["result"]["devices"]
            count = len(devices)
            names = ", ".join([d.get("name", "Unknown") for d in devices])
            send_msg(f"✅ **Eufy Connected!**\nFound {count} Cameras: `{names}`")

        # B. Motion Event
        if data.get("type") == "event" and "event" in data:
            evt = data["event"]
            evt_name = evt.get("name", "").lower()
            
            # Filter: Sirf Motion ya Person events
            if "motion" in evt_name or "person" in evt_name:
                sn = evt.get("serialNumber")
                if sn:
                    print(f"👀 Motion seen on {sn}")
                    threading.Thread(target=send_alert, args=(sn,)).start()

    except Exception as e:
        print(f"JSON Error: {e}")

def start_ws_loop():
    # Node Driver ko start hone ka time dein
    print("⏳ Waiting 20s for Driver...")
    time.sleep(20)
    
    while True:
        try:
            print("🔌 Connecting to Eufy Driver...")
            ws = websocket.WebSocketApp(
                WS_URL,
                on_open=lambda ws: (
                    send_msg("🔗 **Bridge Connected!** Fetching cameras..."),
                    ws.send(json.dumps({"command": "device.get_devices", "messageId": "init"}))
                ),
                on_message=on_message,
                on_error=lambda ws, err: print(f"WS Error: {err}")
            )
            ws.run_forever()
        except Exception as e:
            print(f"WS Crash: {e}")
        
        print("🔄 Reconnecting WS in 10s...")
        time.sleep(10)

if __name__ == "__main__":
    # 1. Sabse pehle batao ki script zinda hai
    send_msg("🚀 **System Restarted on Koyeb!**\nInitializing services...")

    # 2. Flask Thread (Port 5000)
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
    
    # 3. WebSocket Thread
    threading.Thread(target=start_ws_loop, daemon=True).start()

    # 4. Telegram Polling (Main Loop)
    # 409 Conflict se bachne ke liye delay aur webhook removal
    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(2)
        print("🤖 Bot Polling Started")
        bot.polling(non_stop=True, interval=2)
    except Exception as e:
        print(f"Polling Error: {e}")
