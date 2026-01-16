import telebot, os, websocket, json, threading, time, requests, subprocess
from flask import Flask
from datetime import datetime
import pytz

# --- 1. CONFIGURATION (Koyeb Secrets se load hoga) ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://127.0.0.1:3000"

# Bot Initialization with Connectivity Check
print("🤖 Starting Telegram Bot...")
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

@app.route('/')
def health():
    return f"System Online | Time: {datetime.now(IST).strftime('%H:%M:%S')}", 200

# --- 2. TIME MONITORING LOGIC ---
def is_monitoring_time():
    now = datetime.now(IST)
    h, m = now.hour, now.minute
    # Window 1: Midnight (12:30 AM - 5:00 AM)
    midnight = (h == 0 and m >= 30) or (1 <= h < 5)
    # Window 2: Morning (8:30 AM - 9:30 AM)
    morning = (h == 8 and m >= 30) or (h == 9 and m <= 30)
    return midnight or morning

# --- 3. ROBUST DELIVERY ENGINE (Text -> Image -> Video) ---
def start_delivery_workflow(sn):
    ts = datetime.now(IST).strftime('%H:%M:%S')
    
    # STEP 1: Instant Insight
    try:
        bot.send_message(CHAT_ID, f"🔔 **MOTION DETECTED**\n📹 Cam: `{sn}`\n⏰ Time: `{ts} IST`\n🛠️ Status: *Gathering Evidence...*", parse_mode="Markdown")
    except Exception as e:
        print(f"Telegram Text Error: {e}")

    try:
        # STEP 2: Photo Capture (5s delay for cloud sync)
        time.sleep(5)
        img_res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=15)
        if img_res.status_code == 200:
            bot.send_photo(CHAT_ID, img_res.content, caption=f"📸 Snapshot at {ts}")
        
        # STEP 3: 30s Video Recording (CPU Optimized)
        bot.send_message(CHAT_ID, "🔄 *Opening Live Stream & Recording Video...*", parse_mode="Markdown")
        requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream")
        time.sleep(10) # Handshake time
        
        vid_file = f"motion_{sn}.mp4"
        # '-c copy' is the secret for 100% CPU Load fix
        cmd = f"ffmpeg -i {API_URL}/api/v1/devices/{sn}/live -t 30 -c copy -y {vid_file}"
        subprocess.run(cmd, shell=True, timeout=120)

        if os.path.exists(vid_file) and os.path.getsize(vid_file) > 0:
            bot.send_message(CHAT_ID, "📤 *Uploading Video to Telegram...*", parse_mode="Markdown")
            with open(vid_file, 'rb') as video:
                bot.send_video(CHAT_ID, video, caption=f"🎥 Recorded Evidence: {ts}")
            os.remove(vid_file)
            bot.send_message(CHAT_ID, "✅ **Workflow Complete.** Returning to Standby.")
        else:
            bot.send_message(CHAT_ID, "⚠️ **Video Warning:** Stream connected but file was empty.")

        requests.post(f"{API_URL}/api/v1/devices/{sn}/stop_livestream")
    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ **Critical Flow Error:** {str(e)}")

# --- 4. WEBSOCKET HANDLERS (No more infinite logs) ---
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "event":
        evt = data.get("event", {})
        # Catching Motion, Person, or Doorbell Ring
        if any(x in evt.get("name", "").lower() for x in ["motion", "person", "ring"]):
            if is_monitoring_time():
                sn = evt.get("serialNumber")
                threading.Thread(target=start_delivery_workflow, args=(sn,)).start()

def on_open(ws):
    print("✅ Successfully connected to Eufy Driver!")
    bot.send_message(CHAT_ID, "🔗 **Connection Established!**\nSystem is now monitoring for motion.\n\nType /status to verify.")
    ws.send(json.dumps({"command": "start_listening", "messageId": "init_L"}))

def run_ws():
    while True:
        try:
            # Using 127.0.0.1 to avoid DNS resolution issues
            ws = websocket.WebSocketApp("ws://127.0.0.1:3000",
                                      on_open=on_open,
                                      on_message=on_message,
                                      on_error=lambda ws, e: print(f"WS Connection Error: {e}"))
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            time.sleep(10) # Prevent log flooding

# --- 5. INTERACTIVE COMMANDS ---
@bot.message_handler(commands=['status'])
def send_status(message):
    now = datetime.now(IST).strftime('%H:%M:%S')
    monitoring = "🟢 ACTIVE" if is_monitoring_time() else "🟡 STANDBY (Outside Window)"
    try:
        res = requests.get(f"{API_URL}/api/v1/config", timeout=5)
        driver = "✅ Connected" if res.status_code == 200 else "⚠️ Issues"
    except:
        driver = "❌ Offline"
    
    bot.reply_to(message, f"📊 **System Status**\n\n⏰ Time: `{now} IST`\n🛡️ Mode: {monitoring}\n🔌 Driver: {driver}\n⚡ CPU: Optimized")

if __name__ == "__main__":
    # 1. Start Flask for Koyeb Health Checks
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    
    # 2. Initial Boot Message
    try:
        bot.send_message(CHAT_ID, "🚀 **Final Deployment Online!**\nWaiting for Eufy Driver handshake...")
    except:
        print("❌ Could not send Telegram start message. Check Token/ChatID.")

    # 3. Start the Main WebSocket Loop
    run_ws()
