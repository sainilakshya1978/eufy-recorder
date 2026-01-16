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

# Last Motion Time Tracker for Insight
last_motion_time = "No motion yet"

@app.route('/')
def health(): return f"Status: Running | Last Motion: {last_motion_time}", 200

def is_monitoring_time():
    now = datetime.now(IST)
    h, m = now.hour, now.minute
    midnight = (h == 0 and m >= 30) or (1 <= h < 5)
    morning = (h == 8 and m >= 30) or (h == 9 and m <= 30)
    return midnight or morning

def deliver_full_alert(sn):
    global last_motion_time
    ts = datetime.now(IST).strftime('%H:%M:%S')
    last_motion_time = ts
    
    bot.send_message(CHAT_ID, f"🔔 **Activity Detected!**\n📹 Sensor: `{sn}`\n⏰ Time: `{ts}`\n🛠️ Status: *Processing...*", parse_mode="Markdown")

    try:
        time.sleep(5)
        img_res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=15)
        if img_res.status_code == 200:
            bot.send_photo(CHAT_ID, img_res.content, caption=f"📸 Snapshot at {ts}")
        
        bot.send_message(CHAT_ID, "🔄 *Capturing 30s Video Evidence...*", parse_mode="Markdown")
        requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream")
        time.sleep(10)
        
        vid_file = f"motion_{sn}.mp4"
        # CPU OPTIMIZED: -c copy ensures 100% CPU load fix
        cmd = f"ffmpeg -i {API_URL}/api/v1/devices/{sn}/live -t 30 -c copy -y {vid_file}"
        subprocess.run(cmd, shell=True, timeout=120)

        if os.path.exists(vid_file) and os.path.getsize(vid_file) > 0:
            with open(vid_file, 'rb') as video:
                bot.send_video(CHAT_ID, video, caption=f"🎥 Full Record: {ts}")
            os.remove(vid_file)
            bot.send_message(CHAT_ID, "✅ **Workflow Complete.** Standby mode.")
        
        requests.post(f"{API_URL}/api/v1/devices/{sn}/stop_livestream")
    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ **Alert Error:** {str(e)}")

# --- WebSocket Listener with Robust Reconnect ---
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
            print("🔗 Connecting to Eufy Driver WS...")
            ws = websocket.WebSocketApp(f"ws://127.0.0.1:3000", 
                on_open=lambda ws: ws.send(json.dumps({"command": "start_listening", "messageId": "L"})),
                on_message=on_message)
            ws.run_forever()
        except Exception as e:
            print(f"WS Error: {e}. Retrying in 10s...")
            time.sleep(10)

if __name__ == "__main__":
    # Start Health Check Server
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    
    # Telegram Start Confirmation
    try:
        bot.send_message(CHAT_ID, "🚀 **System Robust & Live!**\n\nMonitoring:\n🌙 12:30 AM - 5:00 AM\n☀️ 8:30 AM - 9:30 AM")
    except: pass

    # Keep the main thread alive forever
    run_ws()
