import telebot, os, websocket, json, threading, time, socket
import urllib.request
from flask import Flask
from datetime import datetime

# --- Config ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# FIX: Port 3000 (Matches Driver Log) and Container IP for stable internal connection
WS_URL = "ws://172.17.0.1:3000"  
API_URL = "http://172.17.0.1:3000"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Helper ---
def send_msg(text):
    try:
        print(f"📤 TG: {text}", flush=True)
        bot.send_message(CHAT_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"⚠️ TG Error: {e}", flush=True)

@app.route('/')
def health(): return "Healthy", 200

# --- Status Command ---
@bot.message_handler(commands=['status', 'start'])
def status(m):
    bot.reply_to(m, "✅ **Bot Online!**\n🔌 Driver: Connected\n👀 Monitoring: 24/7")

# --- Media Utility ---
def download_media(url):
    req = urllib.request.Request(
        url, 
        data=None, 
        headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'}
    )
    with urllib.request.urlopen(req) as response:
        return response.read()

# --- 3. Video Worker ---
def fetch_video_background(sn):
    time.sleep(18) # Wait for SD Card write
    try:
        url = f"{API_URL}/api/v1/devices/{sn}/last_video"
        video_data = download_media(url)
        bot.send_video(CHAT_ID, video_data, caption="🎥 Evidence Video (SD Card)")
    except Exception as e:
        print(f"❌ Video Fetch Failed: {e}", flush=True)

# --- Alert Logic ---
def send_alert(sn, event_type):
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    # 1. TEXT ALERT (Instant)
    send_msg(f"🚨 **MOTION DETECTED!**\n📹 Cam: `{sn}`\n⏰ Time: `{timestamp}`")

    # 2. IMAGE ALERT (Fast)
    try:
        time.sleep(2) 
        url = f"{API_URL}/api/v1/devices/{sn}/last_image"
        image_data = download_media(url)
        bot.send_photo(CHAT_ID, image_data, caption="📸 Snapshot")
    except Exception as e:
        print(f"❌ Image Error: {e}", flush=True)

    # 3. VIDEO ALERT (Background)
    threading.Thread(target=fetch_video_background, args=(sn,)).start()

# --- WebSocket Listener ---
def on_open(ws):
    print("✅✅ SOCKET CONNECTED TO PORT 3000 ✅✅", flush=True)
    send_msg("🔗 **Eufy Bridge Connected!** System Armed.")
    ws.send(json.dumps({"command": "start_listening", "messageId": "start"}))
    ws.send(json.dumps({"command": "device.get_devices", "messageId": "init"}))

def on_message(ws, message):
    try:
        data = json.loads(message)
        
        if data.get("type") == "event" and "event" in data:
            evt = data["event"]
            name = evt.get("name", "").lower()
            sn = evt.get("serialNumber")
            
            if sn and any(x in name for x in ["motion", "person", "pet", "ring"]):
                threading.Thread(target=send_alert, args=(sn, name)).start()
        
        elif data.get("type") == "result" and "devices" in data.get("result", {}):
             send_msg(f"✅ **Driver Ready!** Found {len(data['result']['devices'])} devices.")

    except Exception as e:
        print(f"⚠️ Error: {e}", flush=True)

def on_error(ws, error):
    print(f"❌ Socket Error: {error}", flush=True)

def on_close(ws, close_status_code, close_msg):
    print("❌ Socket Closed. Reconnecting...", flush=True)

def start_ws_loop():
    print("🔄 Connecting to Driver (Port 3000)...", flush=True)
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
        time.sleep(10)

if __name__ == "__main__":
    send_msg("🚀 **Bot Restarting.** (Checking Connection...)")
    
    # Flask for Health Check
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
    
    # Wait for Driver to stabilize before Python starts connecting
    time.sleep(35) 
    
    # Start WebSocket Listener
    threading.Thread(target=start_ws_loop, daemon=True).start()
    
    # Start Telegram Polling
    try:
        bot.delete_webhook(drop_pending_updates=True)
        bot.polling(non_stop=True, interval=5)
    except: pass
