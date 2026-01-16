import telebot, os, websocket, json, threading, time, requests, subprocess
from flask import Flask
from datetime import datetime
import pytz

# --- 1. Configuration ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://127.0.0.1:3000"

# --- 2. Telegram Bot Setup ---
print("🤖 Initializing Telegram Bot...")
try:
    bot = telebot.TeleBot(BOT_TOKEN)
    me = bot.get_me()
    print(f"✅ Bot Connected: @{me.username}")
    bot.send_message(CHAT_ID, "🚀 **Final Deployment Started!**\nWaiting for Eufy Driver connection...")
except Exception as e:
    print(f"❌ FATAL: Bot Token Error: {e}")

app = Flask(__name__)

@app.route('/')
def health(): return "System Healthy & Running", 200

# --- 3. Time Monitoring Logic (Midnight + Morning) ---
def is_monitoring_time():
    now = datetime.now(IST)
    h, m = now.hour, now.minute
    
    # Window 1: Midnight (12:30 AM - 5:00 AM)
    midnight = (h == 0 and m >= 30) or (1 <= h < 5)
    
    # Window 2: Morning (8:30 AM - 9:30 AM)
    morning = (h == 8 and m >= 30) or (h == 9 and m <= 30)
    
    return midnight or morning

# --- 4. Robust Delivery Engine (Text -> Image -> Video) ---
def process_alert(sn):
    ts = datetime.now(IST).strftime('%H:%M:%S')
    
    # A. Text Alert
    print(f"🔔 Motion at {ts}. Sending Alert...")
    bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED**\n📹 Cam: `{sn}`\n⏰ Time: `{ts}`", parse_mode="Markdown")

    try:
        # B. Image Snapshot (Wait 5s)
        time.sleep(5)
        img_res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=10)
        if img_res.status_code == 200:
            bot.send_photo(CHAT_ID, img_res.content, caption="📸 Activity Snapshot")

        # C. Video Recording (Optimized)
        bot.send_message(CHAT_ID, "🎥 **Recording 30s Clip...**")
        requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream")
        time.sleep(10) # Handshake wait
        
        vid_file = f"evidence_{sn}.mp4"
        # CPU Fix: -c copy use kiya hai
        cmd = f"ffmpeg -i {API_URL}/api/v1/devices/{sn}/live -t 30 -c copy -y {vid_file}"
        subprocess.run(cmd, shell=True, timeout=90)

        if os.path.exists(vid_file) and os.path.getsize(vid_file) > 0:
            with open(vid_file, 'rb') as video:
                bot.send_video(CHAT_ID, video, caption=f"📼 Evidence: {ts}")
            os.remove(vid_file)
        
        requests.post(f"{API_URL}/api/v1/devices/{sn}/stop_livestream")
        bot.send_message(CHAT_ID, "✅ **Workflow Complete.**")

    except Exception as e:
        bot.send_message(CHAT_ID, f"⚠️ Error during capture: {e}")

# --- 5. WebSocket Logic (The Fix) ---
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "event":
        evt = data.get("event", {})
        # Filter for Motion events
        if any(x in evt.get("name", "").lower() for x in ["motion", "person", "ring"]):
            if is_monitoring_time():
                sn = evt.get("serialNumber")
                threading.Thread(target=process_alert, args=(sn,)).start()
            else:
                print("💤 Motion detected outside monitoring hours.")

def on_error(ws, error):
    print(f"❌ WS Error: {error}")

def on_open(ws):
    print("✅ Connected to Eufy Driver!")
    bot.send_message(CHAT_ID, "🔗 **Eufy Driver Connected!**\n\n🛡️ **System Armed:**\n🌙 12:30 AM - 5:00 AM\n☀️ 08:30 AM - 09:30 AM")
    # Command to start receiving events
    ws.send(json.dumps({"command": "start_listening", "messageId": "init"}))

def run_ws():
    while True:
        try:
            # Explicitly connecting to 127.0.0.1
            ws = websocket.WebSocketApp("ws://127.0.0.1:3000",
                                      on_open=on_open,
                                      on_message=on_message,
                                      on_error=on_error)
            ws.run_forever()
        except Exception as e:
            print(f"⚠️ Reconnection in 5s... ({e})")
            time.sleep(5)

if __name__ == "__main__":
    # Flask Health Check
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    run_ws()
