import telebot, os, websocket, json, threading, time, requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from datetime import datetime
import pytz

# --- 1. SYSTEM CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://localhost:3000" 

print("⚡ Initializing Titanium Hybrid Engine (Photo + SD Card Link)...")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

last_trigger = {}
COOLDOWN_SECONDS = 30 

@app.route('/')
def health():
    return f"Titanium Hybrid Engine Online | Time: {datetime.now(IST).strftime('%H:%M:%S')}", 200

# --- 2. TELEGRAM BUTTON GENERATOR ---
def get_dashboard_markup():
    markup = InlineKeyboardMarkup()
    # Eufy Web Portal link as fallback, usually opening on mobile redirects to the App if configured
    btn_video = InlineKeyboardButton("📹 View Full Video (Open Eufy)", url="https://mysecurity.eufylife.com/")
    markup.add(btn_video)
    return markup

# --- 3. THE INTERCEPTOR WORKFLOW ---
def execute_delivery(sn, trigger_type="Auto", payload=None):
    ts_now = datetime.now(IST)
    ts = ts_now.strftime('%H:%M:%S')
    
    try:
        bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED ({trigger_type})**\n📹 Cam: `{sn}`\n⏰ {ts} IST")
    except: pass 

    time.sleep(4) # Wait for Eufy Cloud to push the notification
    img_bytes = None

    # Deep Search the JSON payload for the hidden image bytes
    def find_image(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ["picture", "thumbnail", "image"] and isinstance(v, dict):
                    if "value" in v and isinstance(v["value"], dict) and "data" in v["value"]:
                        return bytes(v["value"]["data"])
                    elif "data" in v:
                        return bytes(v["data"])
                elif isinstance(v, (dict, list)):
                    found = find_image(v)
                    if found: return found
        return None

    # Attempt 1: Direct from REST API Cache
    try:
        res = requests.get(f"{API_URL}/api/v1/devices/{sn}", timeout=10)
        img_bytes = find_image(res.json())
    except: pass

    # Attempt 2: last_image API Endpoint
    if not img_bytes or len(img_bytes) < 1000:
        try:
            res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=10)
            if res.status_code == 200 and len(res.content) > 1000:
                img_bytes = res.content
        except: pass

    # 📤 SEND PHOTO WITH INTERACTIVE BUTTON
    if img_bytes and len(img_bytes) > 1000:
        try:
            caption = f"📸 **INSTANT PHOTO SECURED**\n⏰ Time: {ts}\n💾 *Video is saving to Camera SD Card.*"
            bot.send_photo(CHAT_ID, img_bytes, caption=caption, reply_markup=get_dashboard_markup())
        except Exception as e:
            bot.send_message(CHAT_ID, f"⚠️ Error sending photo: {e}")
    else:
        # If testing manually without physical motion, photo will not exist.
        msg = f"⚠️ **Photo Not Generated.**\n\nIf this was a Manual Test, no photo is created because no physical motion occurred.\n\n*If this was real motion, ensure Eufy App -> Notifications -> 'Include Thumbnail' is ON.*"
        bot.send_message(CHAT_ID, msg, reply_markup=get_dashboard_markup())

# --- 4. THE FAIL-SAFE LISTENER ---
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "event":
        evt = data.get("event", {})
        if any(x in evt.get("name", "").lower() for x in ["motion", "person", "ring"]):
            sn = evt.get("serialNumber")
            now = time.time()
            
            if sn not in last_trigger or (now - last_trigger[sn]) > COOLDOWN_SECONDS:
                last_trigger[sn] = now
                threading.Thread(target=execute_delivery, args=(sn, "Auto", data)).start()

def on_open(ws):
    print("✅ System 100% Armed!")
    bot.send_message(CHAT_ID, "🟢 **TITANIUM SYSTEM ONLINE (Hybrid SD-Card Edition)**")
    ws.send(json.dumps({"command": "start_listening", "messageId": "init_L"}))

def run_ws():
    time.sleep(10) 
    while True:
        try:
            ws = websocket.WebSocketApp("ws://localhost:3000", on_open=on_open, on_message=on_message)
            ws.run_forever(ping_interval=30, ping_timeout=10)
            time.sleep(5) 
        except:
            time.sleep(10) 

# --- 5. MANUAL COMMANDS ---
@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, f"📊 **System Status**\n🛡️ Mode: 🟢 Active\n⚡ Engine: Photo Interceptor + SD Card Link")

@bot.message_handler(commands=['test'])
def manual_test(message):
    bot.reply_to(message, "🧪 **Initiating Test...** (Reminder: Photo requires physical motion)")
    threading.Thread(target=execute_delivery, args=("T8W11P40240109D4", "Manual Test")).start()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    time.sleep(2)
    run_ws()
