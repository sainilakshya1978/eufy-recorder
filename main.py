import telebot, os, websocket, json, threading, time, requests, subprocess
from flask import Flask
from datetime import datetime
import pytz

# --- Configuration ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://127.0.0.1:3000"

# Bot Initialize
try:
    bot = telebot.TeleBot(BOT_TOKEN)
except Exception as e:
    print(f"❌ Token Error: {e}")

app = Flask(__name__)

@app.route('/')
def health(): return "Optimized System Online", 200

# --- 🕒 ADVANCED DUAL TIME LOGIC 🕒 ---
def is_monitoring_time():
    now = datetime.now(IST)
    h, m = now.hour, now.minute
    
    # 🌙 Window 1: Midnight (12:30 AM to 5:00 AM)
    midnight_window = (h == 0 and m >= 30) or (1 <= h < 5)
    
    # ☀️ Window 2: Morning (8:30 AM to 9:30 AM)
    # Logic: 8:30 se 8:59 tak OR 9:00 se 9:30 tak
    morning_window = (h == 8 and m >= 30) or (h == 9 and m <= 30)
    
    return midnight_window or morning_window

# --- 🚀 CPU OPTIMIZED DELIVERY ENGINE 🚀 ---
def robust_delivery(sn):
    ts = datetime.now(IST).strftime('%H:%M:%S')
    print(f"⚡ Motion detected on {sn} at {ts}!")
    
    # 1. Text Notification (Instant)
    try:
        bot.send_message(CHAT_ID, f"🚨 **MOTION ALERT**\n📹 Cam: `{sn}`\n⏰ Time: `{ts} IST`", parse_mode="Markdown")
    except: pass

    try:
        # 2. Image (Wait 5s for Cloud Sync)
        time.sleep(5)
        img_res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=10)
        if img_res.status_code == 200:
            bot.send_photo(CHAT_ID, img_res.content, caption="📸 Snapshot")

        # 3. Video (Optimized FFmpeg for low CPU)
        requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream")
        time.sleep(8) # Handshake wait
        
        vid_file = f"motion_{sn}.mp4"
        # CPU OPTIMIZATION: '-c copy' is key! It stops re-encoding, saving 90% CPU.
        cmd = f"ffmpeg -i {API_URL}/api/v1/devices/{sn}/live -t 30 -c copy -y {vid_file}"
        subprocess.run(cmd, shell=True, timeout=90)

        if os.path.exists(vid_file) and os.path.getsize(vid_file) > 0:
            with open(vid_file, 'rb') as video:
                bot.send_video(CHAT_ID, video, caption=f"🎥 Evidence (8:30-9:30 AM / Midnight Mode)")
            os.remove(vid_file)
        
        requests.post(f"{API_URL}/api/v1/devices/{sn}/stop_livestream")
    except Exception as e:
        print(f"⚠️ Delivery Error: {e}")

# --- WebSocket Listener (Non-Blocking) ---
def on_message(ws, message):
    try:
        data = json.loads(message)
        if data.get("type") == "event":
            evt = data.get("event", {})
            # Filtering specific events
            if any(x in evt.get("name", "").lower() for x in ["motion", "person", "ring"]):
                if is_monitoring_time():
                    sn = evt.get("serialNumber")
                    # Threading helps main loop stay free
                    threading.Thread(target=robust_delivery, args=(sn,)).start()
                else:
                    # CPU Saving: Agar time nahi hai, toh turant ignore karo
                    pass 
    except: pass

def run_ws():
    while True:
        try:
            # CPU Fix: WebSocket keep-alive connection
            ws = websocket.WebSocketApp(f"ws://127.0.0.1:3000", 
                on_open=lambda ws: ws.send(json.dumps({"command": "start_listening", "messageId": "L"})),
                on_message=on_message)
            ws.run_forever()
        except: 
            time.sleep(20) # Agar crash ho, toh 20s rest karo (CPU saver)

if __name__ == "__main__":
    # Flask Health Check
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    
    # Confirmation Message
    try:
        bot.send_message(CHAT_ID, "✨ **Update Successful!** ✨\n🛡️ Monitoring Zones:\n1️⃣ Midnight: 12:30 AM - 05:00 AM\n2️⃣ Morning: 08:30 AM - 09:30 AM")
    except: pass

    run_ws()
