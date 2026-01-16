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
def health(): return "Insight System Online", 200

# Monitoring Windows: Midnight (12:30-5:00) & Morning (8:30-9:30)
def is_monitoring_time():
    now = datetime.now(IST)
    h, m = now.hour, now.minute
    midnight = (h == 0 and m >= 30) or (1 <= h < 5)
    morning = (h == 8 and m >= 30) or (h == 9 and m <= 30)
    return midnight or morning

# --- Full Insight Delivery Engine ---
def robust_delivery(sn):
    ts = datetime.now(IST).strftime('%H:%M:%S')
    
    # 1. Start Insight
    bot.send_message(CHAT_ID, f"🔔 **Activity Detected!**\n📹 Sensor: `{sn}`\n⏰ Time: `{ts}`\n🛠️ Status: *Processing media...*", parse_mode="Markdown")

    try:
        # 2. Image Process Insight
        time.sleep(5)
        img_res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=10)
        if img_res.status_code == 200:
            bot.send_photo(CHAT_ID, img_res.content, caption=f"📸 Snapshot captured at {ts}")
        
        # 3. Video Process Insight
        bot.send_message(CHAT_ID, "🔄 *Video Stream Starting...* (FFmpeg Handshake)", parse_mode="Markdown")
        requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream")
        time.sleep(8)
        
        vid_file = f"motion_{sn}.mp4"
        # Optimized with -c copy for 0% Re-encoding CPU load
        cmd = f"ffmpeg -i {API_URL}/api/v1/devices/{sn}/live -t 30 -c copy -y {vid_file}"
        subprocess.run(cmd, shell=True, timeout=90)

        if os.path.exists(vid_file) and os.path.getsize(vid_file) > 0:
            bot.send_message(CHAT_ID, "📤 *Uploading 30s Video Evidence...*", parse_mode="Markdown")
            with open(vid_file, 'rb') as video:
                bot.send_video(CHAT_ID, video, caption=f"🎥 Full Record: {ts}")
            os.remove(vid_file)
            bot.send_message(CHAT_ID, "✅ **Workflow Complete.** System back to Standby.")
        else:
            bot.send_message(CHAT_ID, "⚠️ **Video Note:** Stream connected but no frames captured.")
        
        requests.post(f"{API_URL}/api/v1/devices/{sn}/stop_livestream")
    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ **Process Error:** {str(e)}")

# --- Bot Commands ---
@bot.message_handler(commands=['status'])
def status_report(message):
    now = datetime.now(IST).strftime('%H:%M:%S')
    active = "🟢 MONITORING" if is_monitoring_time() else "🟡 STANDBY"
    try:
        requests.get(f"{API_URL}/api/v1/config", timeout=5)
        driver = "✅ Driver Connected"
    except: driver = "❌ Driver Offline"
    
    report = (f"🤖 **System Insight Report**\n\n"
              f"⏱️ Time: `{now} IST`\n"
              f"🛡️ State: {active}\n"
              f"🔌 Link: {driver}\n"
              f"⚡ CPU: Optimized (-c copy)")
    bot.send_message(CHAT_ID, report, parse_mode="Markdown")

# --- WebSocket Listener ---
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "event":
        evt = data.get("event", {})
        if any(x in evt.get("name", "").lower() for x in ["motion", "person", "ring"]):
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
        except: time.sleep
