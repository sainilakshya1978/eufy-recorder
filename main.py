import telebot, os, websocket, json, threading, time
import urllib.request
from flask import Flask
from datetime import datetime

# --- Config ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
WS_URL = "ws://127.0.0.1:3000"  # Port 3000 Fixed
API_URL = "http://127.0.0.1:3000"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Helper ---
def send_msg(text):
    try:
        print(f"📤 TG: {text}", flush=True)
        bot.send_message(CHAT_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"⚠️ TG Fail: {e}", flush=True)

@app.route('/')
def health(): return "System Online", 200

# --- 3. Video Worker (Background Process) ---
def fetch_video_background(sn):
    # Yeh alag thread mein chalega taaki Photo na ruke
    print("⏳ Video processing started (SD Card mode)...", flush=True)
    time.sleep(12) # Camera needs time to finish recording & save to SD card
    
    try:
        url = f"{API_URL}/api/v1/devices/{sn}/last_video"
        print(f"🎥 Downloading Video: {url}", flush=True)
        
        # Download video to memory
        with urllib.request.urlopen(url) as response:
            video_data = response.read()
            
            # Send to Telegram (Viewable Format)
            bot.send_video(CHAT_ID, video_data, caption="🎥 Event Video (Saved on SD Card)")
            print("🎥 Video Sent Successfully!", flush=True)
            
    except Exception as e:
        print(f"❌ Video Fetch Failed: {e}", flush=True)

# --- Alert Logic ---
def send_alert(sn, event_type):
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    # 1. TEXT ALERT (Instant)
    send_msg(f"🚨 **MOTION DETECTED!**\n📹 Camera: `{sn}`\n⚠️ Event: `{event_type}`\n⏰ Time: `{timestamp}`")

    # 2. IMAGE ALERT (Fast - 2 sec delay)
    try:
        time.sleep(2) # Thumbnail generate hone ka chota wait
        url = f"{API_URL}/api/v1/devices/{sn}/last_image"
        
        with urllib.request.urlopen(url) as response:
            image_data = response.read()
            bot.send_photo(CHAT_ID, image_data, caption="📸 Snapshot")
            print("📸 Image Sent!", flush=True)
            
    except Exception as e:
        print(f"❌ Image Error: {e}", flush=True)

    # 3. VIDEO ALERT (Starts independent thread)
    # Isko alag thread mein daal diya taaki Image fast deliver ho
    threading.Thread(target=fetch_video_background, args=(sn,)).start()

# --- WebSocket Listener ---
def on_open(ws):
    print("✅✅ CONNECTED TO EUFY DRIVER (PORT 3000) ✅✅", flush=True)
    send_msg("🔗 **System Ready!** waiting for motion...")
    # Initialize connection
    ws.send(json.dumps({"command": "start_listening", "messageId": "start_listen"}))
    ws.send(json.dumps({"command": "device.get_devices", "messageId": "init"}))

def on_message(ws, message):
    try:
        data = json.loads(message)
        
        # Keep logs clean (Only show events)
        if data.get("type") == "event":
            evt = data["event"]
            evt_name = evt.get("name", "").lower()
            sn = evt.get("serialNumber")
            
            print(f"🔔 EVENT RECEIVED: {evt_name} | SN: {sn}", flush=True)

            # Detect Motion, Person, Pet, Doorbell Ring
            if sn and any(x in evt_name for x in ["motion", "person", "pet", "cross", "ring"]):
                # Thread start karein taaki main loop na ruke
                threading.Thread(target=send_alert, args=(sn, evt_name)).start()

        # Connect Check
        elif data.get("type") == "result" and "devices" in data.get("result", {}):
            print(f"✅ Devices Found: {len(data['result']['devices'])}", flush=True)

    except Exception as e:
        print(f"⚠️ Error parsing: {e}", flush=True)

def on_error(ws, error):
    print(f"❌ Connection Error: {error}", flush=True)

def on_close(ws, close_status_code, close_msg):
    print("❌ Connection Closed. Reconnecting...", flush=True)

def start_ws_loop():
    time.sleep(10) # Initial startup buffer
    print("🚀 Connecting to Driver...", flush=True)
    
    while True:
        try:
            ws = websocket.WebSocketApp(WS_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close)
            ws.run_forever()
        except Exception as e:
            print(f"Critical Error: {e}", flush=True)
        time.sleep(5)

if __name__ == "__main__":
    print("--- BOOTING UP BOT ---", flush=True)
    
    # 1. Flask (Health Check)
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
    
    # 2. WebSocket (Eufy)
    threading.Thread(target=start_ws_loop, daemon=True).start()
    
    # 3. Telegram Polling (Messages)
    time.sleep(20) # 409 Conflict protection
    try:
        bot.delete_webhook(drop_pending_updates=True)
        bot.polling(non_stop=True, interval=2)
    except: pass
