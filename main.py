import telebot, os, websocket, json, threading, time, requests
from flask import Flask
from datetime import datetime
import pytz

# --- 1. SYSTEM CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://localhost:3000" 

print("⚡ Initializing Deep-Search Photo Interceptor...")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

last_trigger = {}
COOLDOWN_SECONDS = 20 

@app.route('/')
def health():
    return f"Titanium Deep-Search Online | Time: {datetime.now(IST).strftime('%H:%M:%S')}", 200

# 🕵️‍♂️ THE HEAVY RESEARCH ALGORITHM: Deep Search for Eufy Buffers
def extract_image_data(obj):
    """Recursively searches the entire Eufy JSON response for ANY picture buffer."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ["picture", "thumbnail", "cover_path", "image"]:
                if isinstance(v, dict):
                    if "value" in v and isinstance(v["value"], dict) and "data" in v["value"]:
                        return bytes(v["value"]["data"])
                    elif "data" in v:
                        return bytes(v["data"])
            elif isinstance(v, (dict, list)):
                found = extract_image_data(v)
                if found: return found
    elif isinstance(obj, list):
        for item in obj:
            found = extract_image_data(item)
            if found: return found
    return None

# --- 2. THE GUARANTEED PHOTO WORKFLOW ---
def execute_delivery(sn, trigger_type="Auto", ws_payload=None):
    ts_now = datetime.now(IST)
    ts = ts_now.strftime('%H:%M:%S')
    
    try:
        bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED ({trigger_type})**\n📹 Cam: `{sn}`\n⏰ {ts} IST\n⚡ Scanning Docker Payload for Photo...")
    except: pass 

    # Wait 4-5 seconds for Eufy Push Notification to arrive at the Docker container
    time.sleep(5)
    img_bytes = None

    # ATTEMPT 1: Check if the photo came directly inside the WebSocket event payload!
    if ws_payload:
        img_bytes = extract_image_data(ws_payload)

    # ATTEMPT 2: Deep Search the REST API Device Cache
    if not img_bytes or len(img_bytes) < 1000:
        try:
            res = requests.get(f"{API_URL}/api/v1/devices/{sn}", timeout=10)
            img_bytes = extract_image_data(res.json())
        except: pass

    # ATTEMPT 3: The standard last_image endpoint
    if not img_bytes or len(img_bytes) < 1000:
        try:
            res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=10)
            if res.status_code == 200 and len(res.content) > 1000:
                img_bytes = res.content
        except: pass

    # 📤 DELIVERY
    if img_bytes and len(img_bytes) > 1000:
        try:
            bot.send_photo(CHAT_ID, img_bytes, caption=f"📸 **EVIDENCE SECURED**\n⏰ Time: {ts}")
        except Exception as e:
            bot.send_message(CHAT_ID, f"⚠️ Error sending photo to Telegram: {e}")
    else:
        bot.send_message(CHAT_ID, f"⚠️ **Photo Not Found in Payload.**\n\nIf this was a '/test', it will ALWAYS fail because Eufy only generates photos for REAL physical motion.\n\nMake sure Eufy App -> Camera Settings -> Notifications -> 'Include Thumbnail' is ON.")

# --- 3. THE WEBSOCKET LISTENER ---
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "event":
        evt = data.get("event", {})
        # Look for motion/person/ring events
        if any(x in evt.get("name", "").lower() or x in evt.get("event", "").lower() for x in ["motion", "person", "ring"]):
            sn = evt.get("serialNumber")
            now = time.time()
            
            if sn not in last_trigger or (now - last_trigger[sn]) > COOLDOWN_SECONDS:
                last_trigger[sn] = now
                # Pass the entire websocket payload to the thread for instant extraction
                threading.Thread(target=execute_delivery, args=(sn, "Real Event", data)).start()

def on_open(ws):
    print("✅ System 100% Armed!")
    bot.send_message(CHAT_ID, "🟢 **TITANIUM SYSTEM ONLINE (Deep-Search Edition)**")
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
    bot.reply_to(message, f"📊 **System Status**\n🛡️ Mode: 🟢 Deep-Search Active")

@bot.message_handler(commands=['test'])
def manual_test(message):
    bot.reply_to(message, "🧪 **Initiating Manual Test...**\n\n⚠️ *NOTE: Because you have no Cloud Subscription, Eufy will NOT generate a photo for manual tests. You MUST physically walk in front of the camera to get a photo.*")
    threading.Thread(target=execute_delivery, args=("T8W11P40240109D4", "Manual Test", None)).start()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    time.sleep(2)
    run_ws()
