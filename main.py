import telebot, os, websocket, json, threading, time
import urllib.request
from flask import Flask
from datetime import datetime

# --- Config ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
WS_URL = "ws://127.0.0.1:3000"
API_URL = "http://127.0.0.1:3000"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Helper ---
def send_msg(text):
    try:
        print(f"📤 TG: {text}", flush=True)
        bot.send_message(CHAT_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"⚠️ TG Error: {e}", flush=True)

# --- Browser Header Hack (Fixes Media Download Error) ---
def download_media(url):
    req = urllib.request.Request(
        url, 
        data=None, 
        headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'
        }
    )
    with urllib.request.urlopen(req) as response:
        return response.read()

# --- Media Worker ---
def fetch_video(sn):
    print("⏳ Video downloading (15s wait)...", flush=True)
    time.sleep(15) 
    try:
        url = f"{API_URL}/api/v1/devices/{sn}/last_video"
        video_data = download_media(url)
        bot.send_video(CHAT_ID, video_data, caption="🎥 Evidence Video")
        print("🎥 Video Sent!", flush=True)
    except Exception as e:
        print(f"❌ Video Error: {e}", flush=True)

# --- Alert Logic ---
def send_alert(sn, event_type):
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    # 1. TEXT (Instant)
    send_msg(f"🚨 **MOTION DETECTED!**\n📹 Camera: `{sn}`\n⚠️ Event: `{event_type}`\n⏰ Time: `{timestamp}`")

    # 2. IMAGE (Fast)
    try:
        time.sleep(1)
        url = f"{API_URL}/api/v1/devices/{sn}/last_image"
        img_data = download_media(url)
        bot.send_photo(CHAT_ID, img_data, caption="📸 Snapshot")
    except Exception as e:
        print(f"❌ Image Error: {e}", flush=True)

    # 3. VIDEO (Background)
    threading.Thread(target=fetch_video, args=(sn,)).start()

# --- WebSocket Listener ---
def on_open(ws):
    print("✅✅ CONNECTED TO DRIVER ✅✅", flush=True)
    send_msg("✅ **System Connected!** Monitoring 24/7.")
    # Initialize
    ws.send(json.dumps({"command": "start_listening", "messageId": "start"}))
    ws.send(json.dumps({"command": "device.get_devices", "messageId": "init"}))

def on_message(ws, message):
    try:
        data = json.loads(message)
        # Check Events
        if data.get("type") == "event" and "event" in data:
            evt = data["event"]
            name = evt.get("name", "").lower()
            sn = evt.get("serialNumber")
            
            print(f"🔔 EVENT: {name}", flush=True)

            if sn and any(x in name for x in ["motion", "person", "pet", "ring"]):
                threading.Thread(target=send_alert, args=(sn, name)).start()
                
    except: pass

def on_error(ws, error):
    # Logs ko connection refused se spam nahi karenge
    pass 

def start_ws_loop():
    print("🔄 Connecting to Driver (Port 3000)...", flush=True)
    while True:
        try:
            ws = websocket.WebSocketApp(WS_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error)
            ws.run_forever()
        except:
            pass
        time.sleep(10) # 10 sec wait before retry

@app.route('/')
def health(): return "Healthy", 200

if __name__ == "__main__":
    send_msg("🚀 **Bot Redeployed**\n(Using 'MyiPhone' Simulation)")
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
    
    time.sleep(20) # Startup Buffer
    threading.Thread(target=start_ws_loop, daemon=True).start()
    
    try:
        bot.delete_webhook(drop_pending_updates=True)
        bot.polling(non_stop=True, interval=5)
    except: pass
