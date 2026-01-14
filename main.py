import telebot, os, websocket, json, threading, time, requests, subprocess
from flask import Flask
from datetime import datetime
import pytz

# --- Configuration (Read from Koyeb Secrets) ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://127.0.0.1:3000"

# Bot Initialize with Error Handling
try:
    bot = telebot.TeleBot(BOT_TOKEN)
    print("✅ Bot object initialized")
except Exception as e:
    print(f"❌ Critical Token Error: {e}")

app = Flask(__name__)

@app.route('/')
def health(): return "100% Robust Logic Online", 200

# Monitoring Window: 12:30 AM to 5:00 AM
def is_monitoring_time():
    now = datetime.now(IST)
    h, m = now.hour, now.minute
    return (h == 0 and m >= 30) or (1 <= h < 5)

# --- The Ultimate Delivery Engine ---
def robust_delivery(sn):
    ts = datetime.now(IST).strftime('%H:%M:%S')
    print(f"🔔 Motion detected on {sn} at {ts}. Starting delivery...")
    
    # 1. Text Notification
    try:
        bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED**\n📹 Cam: `{sn}`\n⏰ Time: `{ts} IST`", parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Failed to send Text: {e}")

    try:
        # 2. Sequential Image (Wait 5s for cloud sync)
        time.sleep(5)
        img_res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=15)
        if img_res.status_code == 200:
            bot.send_photo(CHAT_ID, img_res.content, caption="📸 Activity Snapshot")

        # 3. 30s Video via FFmpeg
        requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream")
        time.sleep(10) # Handshake
        
        vid_file = f"motion_{sn}.mp4"
        cmd = f"ffmpeg -i {API_URL}/api/v1/devices/{sn}/live -t 30 -c copy -y {vid_file}"
        subprocess.run(cmd, shell=True, timeout=120)

        if os.path.exists(vid_file) and os.path.getsize(vid_file) > 0:
            with open(vid_file, 'rb') as video:
                bot.send_video(CHAT_ID, video, caption="🎥 Live Evidence (30s)")
            os.remove(vid_file)
        
        requests.post(f"{API_URL}/api/v1/devices/{sn}/stop_livestream")
    except Exception as e:
        print(f"⚠️ Delivery Flow Error: {e}")

# --- WebSocket Listener ---
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "event":
        evt = data.get("event", {})
        if any(x in evt.get("name", "").lower() for x in ["motion", "person", "ring"]):
            # Trigger ONLY in window
            if is_monitoring_time():
                sn = evt.get("serialNumber")
                threading.Thread(target=robust_delivery, args=(sn,)).start()

def run_ws():
    while True:
        try:
            ws = websocket.WebSocketApp(f"ws://127.0.0.1:3000", 
                on_open=lambda ws: ws.send(json.dumps({"command": "start_listening", "messageId": "L"})),
                on_message=on_message)
            ws.run_forever()
        except: time.sleep(10)

if __name__ == "__main__":
    # Start Health Check Server
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    
    # TELEGRAM CONNECTIVITY TEST
    try:
        me = bot.get_me()
        print(f"✅ Telegram Bot Connected: @{me.username}")
        bot.send_message(CHAT_ID, "🚀 **System Robust & Live!**\nMonitoring Window: 12:30 AM - 5:00 AM.")
    except Exception as e:
        print(f"❌ FATAL: Telegram Connection Refused. Check BOT_TOKEN and CHAT_ID. Error: {e}")

    run_ws()
