import telebot, os, websocket, json, threading, time, requests, subprocess
from flask import Flask
from datetime import datetime
import pytz

# --- 1. SYSTEM CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://localhost:3000" 

print("🤖 Initializing Titanium-Grade Telegram Bot (Zero-Failure Edition)...")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Smart Anti-Crash Lock
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
    vid_file = f"motion_{sn}_{unique_id}.mp4"
    
    try:
        bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED ({trigger_type})**\n📹 Cam: `{sn}`\n⏰ Time: `{ts} IST`\n⚡ Bypassing Cloud. Initializing Direct P2P Tunnel...")
    except: pass # Never crash if Telegram API fluctuates

    try:
        # FAIL-SAFE 2: 45s Timeout for sleeping cameras
        try:
            requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream", timeout=45)
        except Exception as e:
            bot.send_message(CHAT_ID, f"⚠️ P2P Tunnel Timeout: Camera is in deep sleep or offline.")
            return # Exit safely without crashing
            
        bot.send_message(CHAT_ID, "🔄 Tunnel Established (Waiting 15s to stabilize stream)...")
        time.sleep(15) 
        
        # FAIL-SAFE 3: -nostdin prevents FFmpeg from turning into a zombie process and eating CPU
        cmd = f"ffmpeg -nostdin -hide_banner -loglevel error -timeout 15000000 -i {API_URL}/api/v1/devices/{sn}/live -t 30 -c copy -y {vid_file}"
        
        try:
            subprocess.run(cmd, shell=True, timeout=120, check=False)
        except subprocess.TimeoutExpired:
            bot.send_message(CHAT_ID, "⚠️ Extraction took too long. Forcing process kill to save server.")

        # FAIL-SAFE 4: Verifying the file is actually playable ( > 100KB )
        if os.path.exists(vid_file) and os.path.getsize(vid_file) > 100 * 1024:
            with open(vid_file, 'rb') as video:
                bot.send_message(CHAT_ID, "📤 Evidence Secured. Uploading...")
                # High timeout for Telegram upload
                bot.send_video(CHAT_ID, video, caption=f"🎥 Secured Evidence: {ts}", timeout=150)
        else:
            bot.send_message(CHAT_ID, f"⚠️ **Stream Empty:** The camera disconnected before saving 30s of video. Timestamp: {ts}")
            
    except Exception as e:
        try: bot.send_message(CHAT_ID, f"❌ **System Error:** {str(e)[:60]}")
        except: pass
    
    finally:
        # FAIL-SAFE 5: Mandatory Cleanup to prevent Koyeb disk from filling up
        try:
            requests.post(f"{API_URL}/api/v1/devices/{sn}/stop_livestream", timeout=10)
        except: pass
        
        if os.path.exists(vid_file):
            try: os.remove(vid_file)
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
    bot.send_message(CHAT_ID, "🟢 **TITANIUM SYSTEM ONLINE & ARMED (Zero-Failure 24/7 Mode)**")
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
    bot.reply_to(message, f"📊 **System Status**\n⏰ Time: `{now} IST`\n🛡️ Mode: 🟢 24/7 CONTINUOUS\n⚡ Engine: Titanium (Zero-Failure Edition)")

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
