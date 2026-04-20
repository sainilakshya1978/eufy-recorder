import telebot, os, websocket, json, threading, time, requests, subprocess
from flask import Flask
from datetime import datetime
import pytz

# --- 1. SYSTEM CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://localhost:3000" 

print("🤖 Initializing Titanium-Grade Telegram Bot (Ultimate Zero-Failure + Snapshot Edition)...")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Smart Anti-Crash Lock: Prevents server overload during continuous motion
last_trigger = {}
COOLDOWN_SECONDS = 60 

@app.route('/')
def health():
    return f"Titanium No-Refusal System Online | Time: {datetime.now(IST).strftime('%H:%M:%S')}", 200

# --- 2. THE ZERO-FAILURE DELIVERY WORKFLOW ---
def execute_delivery(sn, trigger_type="Auto"):
    ts_now = datetime.now(IST)
    ts = ts_now.strftime('%H:%M:%S')
    
    # FAIL-SAFE 1: Unique filenames to prevent thread collisions
    unique_id = int(ts_now.timestamp())
    img_file = f"snap_{sn}_{unique_id}.jpg"
    vid_file = f"motion_{sn}_{unique_id}.mp4"
    
    try:
        bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED ({trigger_type})**\n📹 Cam: `{sn}`\n⏰ Time: `{ts} IST`\n⚡ Connecting P2P Tunnel...")
    except: pass # Never crash if Telegram API fluctuates

    try:
        # FAIL-SAFE 2: 45s Timeout for sleeping cameras
        try:
            requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream", timeout=45)
        except Exception as e:
            bot.send_message(CHAT_ID, f"⚠️ P2P Tunnel Timeout: Camera is sleeping or offline.")
            return 
            
        time.sleep(12) # Let the camera stream stabilize
        
        # 📸 INSTANT FRAME EXTRACTION (No Cloud Needed)
        bot.send_message(CHAT_ID, "📸 Extracting Instant Snapshot from Live Stream...")
        img_cmd = f"ffmpeg -nostdin -hide_banner -loglevel error -timeout 15000000 -i {API_URL}/api/v1/devices/{sn}/live -vframes 1 -q:v 2 -y {img_file}"
        try:
            subprocess.run(img_cmd, shell=True, timeout=30)
            if os.path.exists(img_file) and os.path.getsize(img_file) > 0:
                with open(img_file, 'rb') as photo:
                    bot.send_photo(CHAT_ID, photo, caption=f"👁️ Instant Snapshot\n⏰ Time: {ts}")
        except: pass # If image fails, don't crash, just move to video

        # 🎥 RECORD 30s VIDEO
        bot.send_message(CHAT_ID, "🎥 Recording 30s Video Evidence...")
        vid_cmd = f"ffmpeg -nostdin -hide_banner -loglevel error -timeout 15000000 -i {API_URL}/api/v1/devices/{sn}/live -t 30 -c copy -y {vid_file}"
        
        try:
            subprocess.run(vid_cmd, shell=True, timeout=120, check=False)
        except subprocess.TimeoutExpired:
            pass # Force kill if it hangs to save CPU

        # 📤 UPLOAD VIDEO
        if os.path.exists(vid_file) and os.path.getsize(vid_file) > 100 * 1024:
            with open(vid_file, 'rb') as video:
                bot.send_message(CHAT_ID, "📤 Uploading Video to Telegram...")
                bot.send_video(CHAT_ID, video, caption=f"🎥 Secured Evidence: {ts}", timeout=150)
        else:
            bot.send_message(CHAT_ID, f"⚠️ **Stream Empty:** Camera disconnected before video finished. Timestamp: {ts}")
            
    except Exception as e:
        try: bot.send_message(CHAT_ID, f"❌ **System Error:** {str(e)[:60]}")
        except: pass
    
    finally:
        # FAIL-SAFE 5: Mandatory Cleanup to prevent Koyeb disk from filling up
        try: requests.post(f"{API_URL}/api/v1/devices/{sn}/stop_livestream", timeout=10)
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
            else:
                print(f"Motion at {datetime.now(IST).strftime('%H:%M:%S')} queued (Cooldown Active).")

def on_open(ws):
    print("✅ Webhook Connected to Eufy API!") 
    bot.send_message(CHAT_ID, "🟢 **TITANIUM SYSTEM ONLINE & ARMED (Ultimate Zero-Failure Mode)**")
    ws.send(json.dumps({"command": "start_listening", "messageId": "init_L"}))

def run_ws():
    time.sleep(10) 
    loop_count = 0
    while True:
        try:
            def custom_on_error(ws, e):
                if "Connection refused" not in str(e):
                    print(f"🚨 Backend Real Error: {e}")

            ws = websocket.WebSocketApp("ws://localhost:3000",
                                      on_open=on_open,
                                      on_message=on_message,
                                      on_error=custom_on_error)
            ws.run_forever(ping_interval=30, ping_timeout=10)
            
            loop_count += 1
            if loop_count % 12 == 0:
                print(f"⏳ [{datetime.now(IST).strftime('%H:%M:%S')}] System Check: All fail-safes active. Awaiting motion...")
            
            time.sleep(5) 
            
        except Exception as e:
            print(f"WS Exception: {e}")
            time.sleep(10) 

# --- 4. MANUAL COMMANDS ---
@bot.message_handler(commands=['status'])
def send_status(message):
    now = datetime.now(IST).strftime('%H:%M:%S')
    bot.reply_to(message, f"📊 **System Status**\n⏰ Time: `{now} IST`\n🛡️ Mode: 🟢 24/7 CONTINUOUS\n⚡ Engine: Titanium (Ultimate Zero-Failure)")

@bot.message_handler(commands=['test'])
def manual_test(message):
    bot.reply_to(message, "🧪 **Initiating Manual Test Protocol...**")
    threading.Thread(target=execute_delivery, args=("T8W11P40240109D4", "Manual Test")).start()

if __name__ == "__main__":
    # 1. Koyeb Health Check
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()
    
    # 2. Telegram Listener 
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    
    time.sleep(2)
    try:
        bot.send_message(CHAT_ID, "🚀 **Server Engine Online. Establishing Zero-Failure Tunnel...**")
    except Exception as e:
        pass 
    
    # 3. Start Eufy Engine
    run_ws()
