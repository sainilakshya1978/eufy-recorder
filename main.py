import telebot, os, websocket, json, threading, time, requests, subprocess
from flask import Flask
from datetime import datetime
import pytz

# --- Configuration ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://127.0.0.1:3000"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def health(): return "System Online", 200

# --- Time Window Check (12:30 AM - 5 AM) ---
def is_monitoring_time():
    now = datetime.now(IST)
    h, m = now.hour, now.minute
    return (h == 0 and m >= 30) or (1 <= h < 5)

# --- Bot Commands (/start & /status) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 **Eufy Security Bot Active!**\n\nI am monitoring your camera from **12:30 AM to 5:00 AM IST**.\n\nCommands:\n/status - Check System Health\n/test - Trigger a live test clip")

@bot.message_handler(commands=['status'])
def send_status(message):
    now = datetime.now(IST).strftime('%H:%M:%S')
    monitoring = "✅ ACTIVE" if is_monitoring_time() else "💤 STANDBY (Outside Window)"
    
    # Driver Check
    try:
        res = requests.get(f"{API_URL}/api/v1/config", timeout=5)
        driver_status = "✅ Connected" if res.status_code == 200 else "⚠️ Driver Issues"
    except:
        driver_status = "❌ Offline"

    status_msg = (
        f"📊 **System Status Report**\n"
        f"⏰ Time: `{now} IST`\n"
        f"🛡️ Monitoring: {monitoring}\n"
        f"🔌 Driver: {driver_status}\n"
        f"☁️ Server: Koyeb Healthy"
    )
    bot.send_message(CHAT_ID, status_msg, parse_mode="Markdown")

# --- Logic for /test (Manual Trigger) ---
@bot.message_handler(commands=['test'])
def manual_test(message):
    bot.send_message(CHAT_ID, "🧪 Starting manual test clip...")
    threading.Thread(target=deliver_full_alert, args=("T8W11P40240109D4",)).start()

# --- Sequential Delivery Engine (The Robust Part) ---
def deliver_full_alert(sn):
    ts = datetime.now(IST).strftime('%H:%M:%S')
    bot.send_message(CHAT_ID, f"🚨 **MONITORING ALERT**\n📹 Cam: `{sn}`\n⏰ Time: `{ts} IST`", parse_mode="Markdown")

    try:
        # Step 1: Image
        time.sleep(5)
        img_res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=15)
        if img_res.status_code == 200:
            bot.send_photo(CHAT_ID, img_res.content, caption=f"📸 Snapshot at {ts}")

        # Step 2: 30s Video
        requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream")
        time.sleep(10)
        vid_file = f"motion_{sn}.mp4"
        cmd = f"ffmpeg -i {API_URL}/api/v1/devices/{sn}/live -t 30 -c copy -y {vid_file}"
        subprocess.run(cmd, shell=True, timeout=100)

        if os.path.exists(vid_file) and os.path.getsize(vid_file) > 0:
            with open(vid_file, 'rb') as video:
                bot.send_video(CHAT_ID, video, caption="🎥 Live Evidence (30s Clip)")
            os.remove(vid_file)
        requests.post(f"{API_URL}/api/v1/devices/{sn}/stop_livestream")
        
    except Exception as e:
        bot.send_message(CHAT_ID, f"⚠️ Error: {str(e)}")

# --- WebSocket & Main Runner ---
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "event":
        evt = data.get("event", {})
        if any(x in evt.get("name", "").lower() for x in ["motion", "person", "ring"]):
            if is_monitoring_time():
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
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    bot.send_message(CHAT_ID, "🚀 **Final Deployment Online!**\nUse /status to check system health.")
    run_ws()
