import telebot, os, websocket, json, threading, time
from flask import Flask
from datetime import datetime

# --- Config ---
# Ensure variables are loaded
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

if not BOT_TOKEN or not CHAT_ID:
    print("❌ ERROR: BOT_TOKEN or CHAT_ID missing in Koyeb Environment Variables")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Health Check (Port 5000) ---
@app.route('/')
def health(): 
    return "Bot is Running", 200

# --- Telegram Helper ---
def send_msg(text):
    try:
        print(f"📤 Sending to TG: {text}")
        bot.send_message(CHAT_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ TG Error: {e}")

# --- Motion Alert Logic ---
def send_alert(sn):
    # 1. Text Alert
    send_msg(f"🚨 **MOTION DETECTED!**\nCamera: `{sn}`\nTime: {datetime.now().strftime('%H:%M:%S')}")
    
    # 2. Media Alert
    try:
        # Image
        time.sleep(2) # Save hone ka time
        bot.send_photo(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image", caption="📸 Snapshot")
        
        # Video
        time.sleep(15) # Video processing time
        bot.send_video(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_video", caption="🎥 Clip")
    except Exception as e:
        print(f"⚠️ Media Error: {e}")

# --- WebSocket Listener ---
def on_message(ws, message):
    try:
        data = json.loads(message)
        
        # 1. Device List Check (Startup par)
        if data.get("type") == "result" and "devices" in data.get("result", {}):
            count = len(data["result"]["devices"])
            send_msg(f"✅ **Connected!** Found {count} Cameras linked to Eufy.")

        # 2. Motion Event Check
        if data.get("type") == "event" and "event" in data:
            evt = data["event"]
            evt_name = evt.get("name", "").lower()
            
            # Sirf Motion ya Person detection par trigger karein
            if "motion" in evt_name or "person" in evt_name:
                sn = evt.get("serialNumber")
                if sn: 
                    print(f"🚨 Motion Detected on {sn}")
                    threading.Thread(target=send_alert, args=(sn,)).start()

    except Exception as e:
        print(f"JSON Error: {e}")

def start_ws():
    # Driver ko start hone ka time dein
    time.sleep(15) 
    while True:
        try:
            ws = websocket.WebSocketApp(
                "ws://127.0.0.1:8000",
                on_open=lambda ws: ws.send(json.dumps({"command": "device.get_devices", "messageId": "init"})),
                on_message=on_message
            )
            ws.run_forever()
        except Exception as e:
            print(f"WS Reconnecting: {e}")
            time.sleep(10)

# --- Main Execution ---
if __name__ == "__main__":
    # 1. Delay to fix 409 Conflict (Old container needs to die)
    print("⏳ Waiting 10s for previous instance to close...")
    time.sleep(10)
    
    # 2. Start Flask & WebSocket
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    threading.Thread(target=start_ws, daemon=True).start()

    # 3. Start Telegram Polling (Safe Mode)
    print("🚀 Bot Started")
    try:
        send_msg("🔄 **Bot Restarted!** Waiting for Eufy Driver...")
        bot.delete_webhook(drop_pending_updates=True)
        bot.polling(non_stop=True, interval=2)
    except Exception as e:
        print(f"Polling Crash: {e}")
