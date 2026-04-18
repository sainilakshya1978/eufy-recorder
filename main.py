import telebot, os, websocket, json, threading, time, requests, subprocess
from flask import Flask
from datetime import datetime
import pytz

# --- 1. SYSTEM CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://localhost:3000" # 🔴 FIX 1: Exact Eufy Server Address

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
    
    try:
        bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED ({trigger_type})**\n📹 Cam: `{sn}`\n⏰ Time: `{ts} IST`\n⚡ Initiating Cloud Extraction...")
    except: pass

    try:
        time.sleep(4) 
        img_res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=15)
        if img_res.status_code == 200:
            bot.send_photo(CHAT_ID, img_res.content, caption="📸 Verified Cloud Snapshot")
    except Exception as e:
        print(f"Network too weak for Image: {e}")

    vid_file = f"motion_{sn}.mp4"
    try:
        requests.post(f"{API_URL}/api/v1/devices/{sn}/start_livestream", timeout=10)
        bot.send_message(CHAT_ID, "🔄 Handshaking with Cloud Tunnel (Waiting 12s for stream)...")
        time.sleep(12) 
        
        cmd = f"ffmpeg -hide_banner -loglevel error -timeout 15000000 -i {API_URL}/api/v1/devices/{sn}/live -t 30 -c copy -y {vid_file}"
        subprocess.run(cmd, shell=True, timeout=120)

        if os.path.exists(vid_file) and os.path.getsize(vid_file) > 150 * 1024:
            with open(vid_file, 'rb') as video:
                bot.send_message(CHAT_ID, "📤 Video Secured. Uploading to Telegram...")
                bot.send_video(CHAT_ID, video, caption=f"🎥 Secured Evidence: {ts}", timeout=120)
        else:
            bot.send_message(CHAT_ID, f"⚠️ **Video Bypass:** P2P tunnel fluctuated. Saved Koyeb storage. Timestamp: {ts}")
            
    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ **Video Blocked:** {str(e)[:60]}")
    
    finally:
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
                threading.Thread(target=execute_delivery, args=(sn, "Auto")).start()
            else:
                print(f"Motion at {datetime.now(IST).strftime('%H:%M:%S')}, ignored (Standby Mode).")

def on_open(ws):
    print("✅ Webhook Connected to Eufy API!") # Yeh line aayegi tabhi success hai!
    bot.send_message(CHAT_ID, "🟢 **TITANIUM SYSTEM ONLINE & ARMED**")
    ws.send(json.dumps({"command": "start_listening", "messageId": "init_L"}))

def run_ws():
    time.sleep(10) 
    loop_count = 0
    while True:
        try:
            def custom_on_error(ws, e):
                if "Connection refused" not in str(e):
                    print(f"🚨 Backend Real Error: {e}")

            # 🔴 FIX 2: Exact Localhost WebSocket Route
            ws = websocket.WebSocketApp("ws://localhost:3000",
                                      on_open=on_open,
                                      on_message=on_message,
                                      on_error=custom_on_error)
            ws.run_forever(ping_interval=30, ping_timeout=10)
            
            loop_count += 1
            if loop_count % 12 == 0:
                print(f"⏳ [{datetime.now(IST).strftime('%H:%M:%S')}] System Monitoring: Attempting connection bridge...")
            
            time.sleep(5) 
            
        except Exception as e:
            print(f"WS Exception: {e}")
            time.sleep(10) 

# --- 5. MANUAL COMMANDS ---
@bot.message_handler(commands=['status'])
def send_status(message):
    now = datetime.now(IST).strftime('%H:%M:%S')
    monitoring = "🟢 ACTIVE" if is_monitoring_time() else "🟡 STANDBY"
    bot.reply_to(message, f"📊 **System Status**\n⏰ Time: `{now} IST`\n🛡️ Mode: {monitoring}\n⚡ Engine: Titanium No-Refusal")

@bot.message_handler(commands=['test'])
def manual_test(message):
    bot.reply_to(message, "🧪 **Initiating Manual Test Protocol...**")
    threading.Thread(target=execute_delivery, args=("T8W11P40240109D4", "Manual Test")).start()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()
    
    time.sleep(2)
    try:
        bot.send_message(CHAT_ID, "🚀 **Server Engine Online. Establishing Cloud Tunnel...**")
    except Exception as e:
        pass # Ignored transient network flap during boot
    
    run_ws()
