import telebot, os, websocket, json, threading, time, requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from datetime import datetime
import pytz
import base64

# --- 1. SYSTEM CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://localhost:3000" 

print("⚡ Initializing Titanium Hunter Engine...")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

last_trigger = {}
COOLDOWN_SECONDS = 30 

@app.route('/')
def health():
    return f"Titanium Hunter Engine Online | Time: {datetime.now(IST).strftime('%H:%M:%S')}", 200

def get_dashboard_markup():
    markup = InlineKeyboardMarkup()
    btn_video = InlineKeyboardButton("📹 View Full Video (Open Eufy)", url="https://mysecurity.eufylife.com/")
    markup.add(btn_video)
    return markup

# 🕵️‍♂️ THE ADVANCED DEEP SEARCH ALGORITHM
def find_image(obj):
    """Ultra-aggressive deep search for image data, including Base64"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ["picture", "thumbnail", "image", "cover_path"] and v:
                if isinstance(v, dict):
                    # Node.js Buffer format
                    if "value" in v and isinstance(v["value"], dict) and "data" in v["value"]:
                        return bytes(v["value"]["data"])
                    elif "data" in v:
                        return bytes(v["data"])
                elif isinstance(v, str):
                    # Base64 string format (JPEG/PNG magic bytes)
                    if v.startswith("/9j/") or v.startswith("iVBORw0KGgo"): 
                        try: return base64.b64decode(v)
                        except: pass
            elif isinstance(v, (dict, list)):
                found = find_image(v)
                if found: return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_image(item)
            if found: return found
    return None

# --- 2. THE HUNTER WORKFLOW ---
def execute_delivery(sn, trigger_type="Auto"):
    ts_now = datetime.now(IST)
    ts = ts_now.strftime('%H:%M:%S')
    
    try:
        bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED ({trigger_type})**\n📹 Cam: `{sn}`\n⏰ {ts} IST\n⏳ Hunting for Eufy thumbnail (Waiting up to 20s)...")
    except: pass 

    img_bytes = None

    # 🎯 THE HUNTER LOOP: Check every 3 seconds for up to 21 seconds
    for attempt in range(7):
        time.sleep(3) 

        # Attempt A: Check standard API cache
        try:
            res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=5)
            if res.status_code == 200 and len(res.content) > 1000:
                img_bytes = res.content
                break # Found it! Break the loop.
        except: pass

        # Attempt B: Deep Search the raw device payload
        try:
            res = requests.get(f"{API_URL}/api/v1/devices/{sn}", timeout=5)
            img_bytes = find_image(res.json())
            if img_bytes and len(img_bytes) > 1000:
                break # Found it! Break the loop.
        except: pass

    # 📤 SEND RESULT
    if img_bytes and len(img_bytes) > 1000:
        try:
            bot.send_photo(CHAT_ID, img_bytes, caption=f"📸 **EVIDENCE SECURED**\n⏰ Time: {ts}\n💾 *Video is on Camera SD Card.*", reply_markup=get_dashboard_markup())
        except Exception as e:
            bot.send_message(CHAT_ID, f"⚠️ Error sending photo: {e}")
    else:
        msg = f"⚠️ **Photo Not Generated.**\n\nCloud did not send a thumbnail within 20 seconds. Ensure Eufy App -> Notifications -> 'Include Thumbnail' is ON."
        bot.send_message(CHAT_ID, msg, reply_markup=get_dashboard_markup())

# --- 3. THE LISTENER ---
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
    bot.send_message(CHAT_ID, "🟢 **TITANIUM SYSTEM ONLINE (Hunter Edition)**")
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
    bot.reply_to(message, f"📊 **System Status**\n🛡️ Mode: 🟢 Active\n⚡ Engine: Photo Hunter")

@bot.message_handler(commands=['test'])
def manual_test(message):
    bot.reply_to(message, "🧪 **Initiating Test...** (Photo requires physical motion)")
    threading.Thread(target=execute_delivery, args=("T8W11P40240109D4", "Manual Test")).start()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    time.sleep(2)
    run_ws()
