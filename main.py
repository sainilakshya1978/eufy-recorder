import telebot, os, websocket, json, threading, time, requests, subprocess
from flask import Flask
from datetime import datetime
import pytz

# --- 1. SYSTEM CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://127.0.0.1:3000"

print("🤖 Initializing Titanium-Grade Telegram Bot...")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def health():
    return f"Titanium No-Refusal System Online | Time: {datetime.now(IST).strftime('%H:%M:%S')}", 200

# --- 2. TIME LOGIC (Strict Windows) ---
def is_monitoring_time():
    now = datetime.now(IST)
    h, m = now.hour, now.minute
    midnight = (h == 0 and m >= 30) or (1 <= h < 5)
    morning = (h == 8 and m >= 30) or (h == 9 and m <= 30)
    return midnight or morning

# --- 3. THE NO-REFUSAL DELIVERY WORKFLOW ---
def execute_delivery(sn, trigger_type="Auto"):
    ts = datetime.now(IST).strftime('%H:%M:%S')
    
    # GUARANTEE 1: The Instant Text Ping
    try:
        bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED ({trigger_type})**\n📹 Cam: `{sn}`\n⏰ Time: `{ts} IST`\n⚡ Initiating Cloud Extraction...")
    except: pass

    # GUARANTEE 2: The Image Pull (Tolerates 15s network drops)
    try:
        time.sleep(4) 
        img_res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=15)
        if img_res.status_code == 200:
            bot.send_photo(CHAT_ID, img_res.content, caption="📸 Verified Cloud Snapshot")
    except Exception as e:
        print(f"Network too weak for Image: {e}")

    # GUARANTEE 3: The Bulletproof Video Extraction
    vid_file = f"motion_{sn}.mp4"
    try:
        # Step A: Request Livestream P2P Tunnel
        requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream", timeout=10)
        bot.send_message(CHAT_ID, "🔄 Handshaking with Cloud Tunnel (Waiting 12s for stream stabilization)...")
        time.sleep(12) 
        
        # Step B: CPU-Optimized, Network-Tolerant FFmpeg Command
        # -timeout 15000000: Waits up to 15s for stream instead of failing instantly.
        # -loglevel error: Stops Koyeb log flooding.
        # -c copy: Zero CPU encoding overhead.
        cmd = f"ffmpeg -hide_banner -loglevel error -timeout 15000000 -i {API_URL}/api/v1/devices/{sn}/live -t 30 -c copy -y {vid_file}"
        subprocess.run(cmd, shell=True, timeout=120)

        # Step C: File Integrity Reality Check (> 150KB size prevents empty files)
        if os.path.exists(vid_file) and os.path.getsize(vid_file) > 150 * 1024:
            with open(vid_file, 'rb') as video:
                bot.send_message(CHAT_ID, "📤 Video Secured. Uploading to Telegram (Timeout fixed)...")
                bot.send_video(CHAT_ID, video, caption=f"🎥 Secured Evidence: {ts}", timeout=120)
        else:
            bot.send_message(CHAT_ID, f"⚠️ **Video Bypass:** P2P tunnel fluctuated or file corrupted. Saved Koyeb storage. Timestamp: {ts}")
            
    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ **Video Blocked:** {str(e)[:60]}")
    
    finally:
        # GUARANTEE 4: Strict Cleanup (Mandatory to save Koyeb 512MB limit)
        try:
            requests.post(f"{API_URL}/api/v1/devices/{sn}/stop_livestream", timeout=5)
        except: pass
        if os.path.exists(vid_file):
            os.remove(vid_file)

# --- 4. WEBSOCKET & AUTO-RECONNECT ---
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "event":
        evt = data.get("event", {})
        if any(x in evt.get("name", "").lower() for x in ["motion", "person", "ring"]):
            if is_monitoring_time():
                sn = evt.get("serialNumber")
                # Spawn separate thread so WebSocket NEVER hangs
                threading.Thread(target=execute_delivery, args=(sn, "Auto")).start()
            else:
                print(f"Motion at {datetime.now(IST).strftime('%H:%M:%S')}, but ignored (Standby Mode).")

def on_open(ws):
    print("✅ Webhook Connected to Eufy API!")
    bot.send_message(CHAT_ID, "🟢 **TITANIUM SYSTEM ONLINE & ARMED**\nMonitoring Windows: 12:30-5:00 AM & 8:30-9:30 AM.")
    ws.send(json.dumps({"command": "start_listening", "messageId": "init_L"}))

def run_ws():
    while True:
        try:
            ws = websocket.WebSocketApp("ws://127.0.0.1:3000",
                                      on_open=on_open,
                                      on_message=on_message,
                                      on_error=lambda ws, e: print(f"WS Error: {e}"))
            # ping_interval prevents Load Balancer disconnects
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            time.sleep(10) # 10s backoff prevents CPU spiking on crash

# --- 5. MANUAL COMMANDS ---
@bot.message_handler(commands=['status'])
def send_status(message):
    now = datetime.now(IST).strftime('%H:%M:%S')
    monitoring = "🟢 ACTIVE" if is_monitoring_time() else "🟡 STANDBY"
    bot.reply_to(message, f"📊 **System Status**\n⏰ Time: `{now} IST`\n🛡️ Mode: {monitoring}\n⚡ Engine: Titanium No-Refusal")

@bot.message_handler(commands=['test'])
def manual_test(message):
    bot.reply_to(message, "🧪 **Initiating Manual Test Protocol...**")
    # T8W11P40240109D4 is your camera SN from previous logs
    threading.Thread(target=execute_delivery, args=("T8W11P40240109D4", "Manual Test")).start()

if __name__ == "__main__":
    # Internal Health Check
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    try:
        bot.send_message(CHAT_ID, "🚀 **Final Deployment Booting... Please wait for 'System Online' signal.**")
    except: pass
    
    # Start driver connection
    run_ws()
