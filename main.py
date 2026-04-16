import telebot, os, websocket, json, threading, time, requests, subprocess
from flask import Flask
from datetime import datetime
import pytz

# --- 1. CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://127.0.0.1:3000"

print("🤖 Initializing Pro-Security Telegram Bot...")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- SYSTEM STATE TRACKERS ---
system_start_time = datetime.now(IST)
is_driver_connected = False

@app.route('/')
def health():
    return f"Pro System Online | Uptime started: {system_start_time.strftime('%H:%M:%S')}", 200

# --- 2. TIME MONITORING LOGIC ---
def is_monitoring_time():
    now = datetime.now(IST)
    h, m = now.hour, now.minute
    midnight = (h == 0 and m >= 30) or (1 <= h < 5)
    morning = (h == 8 and m >= 30) or (h == 9 and m <= 30)
    return midnight or morning

def get_uptime():
    duration = datetime.now(IST) - system_start_time
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{duration.days} Days, {hours} Hrs, {minutes} Mins"

# --- 3. THE NO-REFUSAL DELIVERY WORKFLOW (TEXT -> IMAGE -> VIDEO) ---
def execute_delivery(sn):
    ts = datetime.now(IST).strftime('%H:%M:%S')
    
    # STEP 1: Instant Text (Guaranteed Ping)
    try:
        bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED**\n📹 Cam: `{sn}`\n⏰ Time: `{ts} IST`\n⚡ Extracting secure media...")
    except: pass

    # STEP 2: Image Fetch (Tolerates weak Wi-Fi)
    try:
        time.sleep(5) 
        img_res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=15)
        if img_res.status_code == 200:
            bot.send_photo(CHAT_ID, img_res.content, caption="📸 Verified Snapshot")
    except Exception as e:
        print(f"Network weak for Image: {e}")

    # STEP 3: Video Extraction (The Bulletproof Fix)
    vid_file = f"motion_{sn}.mp4"
    try:
        requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream", timeout=10)
        bot.send_message(CHAT_ID, "🔄 Tunnel active. Recording 30s Video...")
        
        time.sleep(12) # Wait for P2P buffer
        
        # -timeout 15000000 ensures it waits 15s for slow internet streams
        cmd = f"ffmpeg -timeout 15000000 -i {API_URL}/api/v1/devices/{sn}/live -t 30 -c copy -y {vid_file}"
        subprocess.run(cmd, shell=True, timeout=120, capture_output=True)

        if os.path.exists(vid_file) and os.path.getsize(vid_file) > 150 * 1024:
            with open(vid_file, 'rb') as video:
                bot.send_message(CHAT_ID, "📤 Uploading Video to Telegram...")
                bot.send_video(CHAT_ID, video, caption=f"🎥 Secure Evidence: {ts}", timeout=120)
        else:
            bot.send_message(CHAT_ID, f"⚠️ **Video Bypass:** Connection fluctuated. File empty. Timestamp: {ts}")
            
    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ **Video Blocked:** {str(e)[:50]}")
    
    finally:
        # Strict Cleanup
        try:
            requests.post(f"{API_URL}/api/v1/devices/{sn}/stop_livestream", timeout=5)
        except: pass
        if os.path.exists(vid_file):
            os.remove(vid_file)

# --- 4. ROBUST WEBSOCKET & WATCHDOG ---
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "event":
        evt = data.get("event", {})
        if any(x in evt.get("name", "").lower() for x in ["motion", "person", "ring"]):
            if is_monitoring_time():
                sn = evt.get("serialNumber")
                threading.Thread(target=execute_delivery, args=(sn,)).start()

def on_open(ws):
    global is_driver_connected, system_start_time
    is_driver_connected = True
    system_start_time = datetime.now(IST) # Reset uptime on fresh connection
    try:
        bot.send_message(CHAT_ID, f"🟢 **MONITORING STARTED**\n\n🛡️ System is now actively watching.\n⏱️ Start Time: `{system_start_time.strftime('%H:%M:%S')} IST`\n⏰ Active Windows:\n- 12:30 AM to 5:00 AM\n- 8:30 AM to 9:30 AM")
    except: pass

def on_close(ws, close_status_code, close_msg):
    global is_driver_connected
    if is_driver_connected: # Only send if it was previously connected
        is_driver_connected = False
        try:
            uptime = get_uptime()
            bot.send_message(CHAT_ID, f"🔴 **SYSTEM OFFLINE / CONNECTION LOST**\n\n⚠️ Eufy Driver disconnected from Cloud.\n⏱️ Total Uptime Before Drop: `{uptime}`\n🔄 Attempting Auto-Reconnect...")
        except: pass

def on_error(ws, error):
    print(f"WS Error: {error}")

def run_ws():
    while True:
        try:
            ws = websocket.WebSocketApp("ws://127.0.0.1:3000",
                                      on_open=on_open,
                                      on_message=on_message,
                                      on_close=on_close,
                                      on_error=on_error)
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            time.sleep(10) # Prevent CPU spike loop

# --- 5. INTERACTIVE COMMANDS ---
@bot.message_handler(commands=['status'])
def send_status(message):
    now = datetime.now(IST).strftime('%H:%M:%S')
    uptime = get_uptime()
    monitoring = "🟢 ACTIVE" if is_monitoring_time() else "🟡 STANDBY"
    driver = "✅ Connected" if is_driver_connected else "❌ Offline/Reconnecting"
    
    bot.reply_to(message, f"📊 **System Status Report**\n\n⏱️ Current Time: `{now} IST`\n⌛ Continuous Uptime: `{uptime}`\n🛡️ Monitoring Mode: {monitoring}\n🔌 Camera Tunnel: {driver}\n⚡ Engine: No-Refusal")

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    run_ws()
