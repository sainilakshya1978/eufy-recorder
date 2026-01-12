import telebot, os, websocket, json, threading, time
import urllib.request
from flask import Flask
from datetime import datetime

# --- Config ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# Fix: Use 'localhost' matches driver logs
WS_URL = "ws://localhost:3000"
API_URL = "http://localhost:3000"

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
    # Check karein manually ki port open hai ya nahi
    status_msg = "✅ **Bot Online**"
    try:
        urllib.request.urlopen(f"{API_URL}", timeout=1)
        status_msg += "\n🟢 Driver Connection: **Connected**"
    except:
        status_msg += "\n🔴 Driver Connection: **Disconnected (Retrying...)**"
        
    status_msg += "\n👀 Monitoring: 24/7"
    bot.reply_to(m, status_msg)

# --- 3. Video Worker (Background) ---
def fetch_video_background(sn):
    time.sleep(15) # Wait for SD Card save
    try:
        url = f"{API_URL}/api/v1/devices/{sn}/last_video"
        print(f"🎥 Downloading Video: {url}", flush=True)
        with urllib.request.urlopen(url) as response:
            data = response.read()
            bot.send_video(CHAT_ID, data, caption="🎥 Video Evidence (SD Card)")
    except Exception as e:
        print(f"❌ Video Error: {e}", flush=True)

# --- Alert Logic ---
def send_alert(sn, event_type):
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    # 1. TEXT ALERT (Instant)
    send_msg(f"🚨 **MOTION DETECTED!**\n📹 Camera: `{sn}`\n⚠️ Event: `{event_type}`\n⏰ Time: `{timestamp}`")

    # 2. IMAGE ALERT (Fast)
    try:
        time.sleep(2)
        url = f"{API_URL}/api/v1/devices/{sn}/last_image"
        with urllib.request.urlopen(url) as response:
            data = response.read()
            bot.send_photo(CHAT_ID, data, caption="📸 Snapshot")
    except: pass

    # 3. VIDEO ALERT (Background Thread)
    threading.Thread(target=fetch_video_background, args=(sn,)).start()

# --- WebSocket Listener ---
def on_open(ws):
    print("✅✅ SOCKET CONNECTED TO PORT 3000 ✅✅", flush=True)
    send_msg("✅ **Connection Established!**\nSystem is armed and monitoring.")
    # Initialize
    ws.send(json.dumps({"command": "start_listening", "messageId": "start_listen"}))
    ws.send(json.dumps({"command": "device.get_devices", "messageId": "init"}))

def on_message(ws, message):
    try:
        data = json.loads(message)
        
        # Event Logic
        if data.get("type") == "event" and "event" in data:
            evt = data["event"]
            evt_name = evt.get("name", "").lower()
            sn = evt.get("serialNumber")
            
            print(f"🔔 EVENT: {evt_name} | SN: {sn}", flush=True)

            if sn and any(x in evt_name for x in ["motion", "person", "pet", "cross", "ring"]):
                threading.Thread(target=send_alert, args=(sn, evt_name)).start()

    except Exception as e:
        print(f"⚠️ Error: {e}", flush=True)

def on_error(ws, error):
    # Connection Refused errors ko log karein lekin crash na hone dein
    print(f"❌ Socket Error: {error}", flush=True)

def on_close(ws, close_status_code, close_msg):
    print("❌ Socket Closed. Retrying...", flush=True)

def start_ws_loop():
    # Wait loop until Driver is ready
    while True:
        try:
            print("🔄 Attempting to connect to Driver (Port 3000)...", flush=True)
            ws = websocket.WebSocketApp(WS_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close)
            ws.run_forever()
        except Exception as e:
            print(f"Critical Error: {e}", flush=True)
        
        # Agar connect nahi hua (Refused), to 10 second ruk kar fir try karega
        time.sleep(10)

if __name__ == "__main__":
    send_msg("🚀 **Bot Initialized on Koyeb**\n⏳ Waiting for Eufy Driver to startup...")
    
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
    
    # 30 second ka delay taaki Driver start ho sake
    time.sleep(30)
    
    threading.Thread(target=start_ws_loop, daemon=True).start()
    
    try:
        bot.delete_webhook(drop_pending_updates=True)
        bot.polling(non_stop=True, interval=5)
    except: pass
