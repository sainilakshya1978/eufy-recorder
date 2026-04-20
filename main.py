import telebot, os, websocket, json, threading, time, requests, subprocess
from flask import Flask
from datetime import datetime
import pytz

# --- 1. SYSTEM CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://localhost:3000" 

print("🚀 Initializing Space-Grade Telegram Bot (Dual-Core Parallel Edition)...")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Smart Anti-Crash Lock
last_trigger = {}
COOLDOWN_SECONDS = 60 

@app.route('/')
def health():
    return f"Titanium Space System Online | Time: {datetime.now(IST).strftime('%H:%M:%S')}", 200

# --- 2. THE DUAL-CORE SPACE TECH WORKFLOW ---
def execute_delivery(sn, trigger_type="Auto"):
    ts_now = datetime.now(IST)
    ts = ts_now.strftime('%H:%M:%S')
    
    unique_id = int(ts_now.timestamp())
    img_file = f"snap_{sn}_{unique_id}.jpg"
    vid_file = f"motion_{sn}_{unique_id}.mp4"
    
    try:
        bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED ({trigger_type})**\n📹 Cam: `{sn}`\n⏰ Time: `{ts} IST`\n⚡ Booting Space-Tech Engine...")
    except: pass 

    video_process = None
    try:
        # 🔨 STEP 1: TRIPLE-KNOCK WAKE UP (Handles Deep Sleep)
        stream_started = False
        for attempt in range(3): 
            try:
                res = requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream", timeout=25)
                if res.status_code == 200:
                    stream_started = True
                    break 
            except Exception as e:
                time.sleep(5) 
                
        if not stream_started:
            bot.send_message(CHAT_ID, f"⚠️ **Camera Asleep:** Eufy Cloud failed to wake the camera.")
            return 
            
        bot.send_message(CHAT_ID, "✅ Camera Awake! Initiating Dual-Core Extraction...")
        time.sleep(5) # Brief pause for P2P handshake
        
        # 🎥 STEP 2: START VIDEO IMMEDIATELY (Background Process)
        # We start video first so we don't miss a single second of the action!
        vid_cmd = f"ffmpeg -nostdin -y -hide_banner -loglevel error -timeout 15000000 -i {API_URL}/api/v1/devices/{sn}/live -t 30 -c copy {vid_file}"
        video_process = subprocess.Popen(vid_cmd, shell=True)

        # 📸 STEP 3: THE "GHOST" SNIPER (Extract photo FROM the recording video)
        photo_secured = False
        for attempt in range(8): # Check the recording file for 24 seconds max
            time.sleep(3) 
            # Check if video has started saving data to server
            if os.path.exists(vid_file) and os.path.getsize(vid_file) > 50 * 1024: 
                # Tap into the local file and extract the first frame lightning fast!
                img_cmd = f"ffmpeg -nostdin -y -hide_banner -loglevel error -i {vid_file} -vframes 1 -q:v 2 {img_file}"
                subprocess.run(img_cmd, shell=True, timeout=10)
                
                if os.path.exists(img_file) and os.path.getsize(img_file) > 10 * 1024:
                    with open(img_file, 'rb') as photo:
                        bot.send_photo(CHAT_ID, photo, caption=f"📸 **INSTANT AI SNAPSHOT**\n⏰ {ts}")
                    photo_secured = True
                    break # Photo sent! Exit the sniper loop.
        
        if not photo_secured:
            bot.send_message(CHAT_ID, "⚠️ Network fluctuation prevented instant photo. Video is still recording...")

        # ⏳ STEP 4: WAIT FOR VIDEO TO FINISH (Wait up to 45 secs for the 30s video to close)
        try:
            video_process.wait(timeout=45)
        except subprocess.TimeoutExpired:
            pass # Force move on if FFmpeg hangs

        # 📤 STEP 5: UPLOAD VIDEO
        if os.path.exists(vid_file) and os.path.getsize(vid_file) > 150 * 1024:
            with open(vid_file, 'rb') as video:
                bot.send_video(CHAT_ID, video, caption=f"🎥 FULL SECURED EVIDENCE: {ts}", timeout=150)
        else:
            bot.send_message(CHAT_ID, f"⚠️ **Video Truncated:** The subject moved out of frame too quickly.")
            
    except Exception as e:
        try: bot.send_message(CHAT_ID, f"❌ **System Error:** {str(e)[:60]}")
        except: pass
    
    finally:
        # STEP 6: CRITICAL CLEANUP
        try: requests.post(f"{API_URL}/api/v1/devices/{sn}/stop_livestream", timeout=10)
        except: pass
        
        # Kill the ghost process if it got stuck
        if video_process and video_process.poll() is None:
            try: video_process.kill()
            except: pass

        if os.path.exists(vid_file):
            try: os.remove(vid_file)
            except: pass
        if os.path.exists(img_file):
            try: os.remove(img_file)
            except: pass

# --- 3. WEBSOCKET & CONTINUOUS AUTO-RECONNECT ---
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "event":
        evt = data.get("event", {})
        if any(x in evt.get("name", "").lower() for x in ["motion", "person", "ring"]):
            sn = evt.get("serialNumber")
            now = time.time()
            
            if sn not in last_trigger or (now - last_trigger[sn]) > COOLDOWN_SECONDS:
                last_trigger[sn] = now
                threading.Thread(target=execute_delivery, args=(sn, "Auto")).start()

def on_open(ws):
    print("✅ Webhook Connected to Eufy API!") 
    bot.send_message(CHAT_ID, "🟢 **TITANIUM SYSTEM ONLINE & ARMED (Space-Tech Edition)**")
    ws.send(json.dumps({"command": "start_listening", "messageId": "init_L"}))

def run_ws():
    time.sleep(10) 
    while True:
        try:
            def custom_on_error(ws, e):
                if "Connection refused" not in str(e): print(f"🚨 Error: {e}")

            ws = websocket.WebSocketApp("ws://localhost:3000",
                                      on_open=on_open,
                                      on_message=on_message,
                                      on_error=custom_on_error)
            ws.run_forever(ping_interval=30, ping_timeout=10)
            time.sleep(5) 
        except:
            time.sleep(10) 

# --- 4. MANUAL COMMANDS ---
@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, f"📊 **System Status**\n🛡️ Mode: 🟢 24/7 CONTINUOUS\n⚡ Engine: Space-Tech Dual-Core")

@bot.message_handler(commands=['test'])
def manual_test(message):
    bot.reply_to(message, "🧪 **Initiating Manual Test...**")
    threading.Thread(target=execute_delivery, args=("T8W11P40240109D4", "Manual Test")).start()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    time.sleep(2)
    run_ws()
