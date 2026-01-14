import telebot, os, websocket, json, threading, time, requests, subprocess
from flask import Flask
from datetime import datetime
import pytz

# --- Environment Variables ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://127.0.0.1:3000"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def health(): return "System 100% Operational", 200

# --- Sequential Delivery Engine ---
def deliver_full_alert(sn):
    timestamp = datetime.now(IST).strftime('%H:%M:%S')
    
    # STEP 1: Instant Text Alert
    bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED**\n📹 Cam: `{sn}`\n⏰ Time: `{timestamp} IST`", parse_mode="Markdown")

    try:
        # STEP 2: Fast Image Capture (Wait 4s for Cloud Upload)
        time.sleep(4)
        img_res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=10)
        if img_res.status_code == 200:
            bot.send_photo(CHAT_ID, img_res.content, caption="📸 Activity Snapshot")

        # STEP 3: Video Recording (Live via FFmpeg)
        # 30-second clip capture logic
        requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream")
        time.sleep(8) # P2P Handshake
        
        video_file = f"alert_{sn}.mp4"
        cmd = f"ffmpeg -i {API_URL}/api/v1/devices/{sn}/live -t 30 -c copy -y {video_file}"
        subprocess.run(cmd, shell=True, timeout=90)

        if os.path.exists(video_file) and os.path.getsize(video_file) > 0:
            with open(video_file, 'rb') as video:
                bot.send_video(CHAT_ID, video, caption="🎥 Recorded Evidence (30s)")
            os.remove(video_file)
        
        requests.post(f"{API_URL}/api/v1/devices/{sn}/stop_livestream")
        
    except Exception as e:
        print(f"Delivery Error: {e}")

# --- WebSocket Listener ---
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "event":
        evt = data.get("event", {})
        if any(x in evt.get("name", "").lower() for x in ["motion", "person", "ring"]):
            sn = evt.get("serialNumber")
            threading.Thread(target=deliver_full_alert, args=(sn,)).start()

def run_ws():
    while True:
        try:
            ws = websocket.WebSocketApp(f"ws://127.0.0.1:3000", 
                                        on_open=lambda ws: ws.send(json.dumps({"command": "start_listening", "messageId": "L"})),
                                        on_message=on_message)
            ws.run_forever()
        except: time.sleep(10)

if __name__ == "__main__":
    # Start Health Check
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    # Initial Log to Telegram
    bot.send_message(CHAT_ID, "🚀 **Final Deployment Live!** Monitoring started with 100% Delivery Mode.")
    run_ws()
