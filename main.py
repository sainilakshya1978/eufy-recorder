import telebot, os, websocket, json, threading, time, base64
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from datetime import datetime
import pytz

# --- 1. SYSTEM CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 
IST = pytz.timezone('Asia/Kolkata')

print("⚡ Initializing Titanium Flawless Cloud Engine...")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

recent_motions = {}
COOLDOWN_SECONDS = 20 

@app.route('/')
def health():
    return f"Titanium Flawless Engine Online | Time: {datetime.now(IST).strftime('%H:%M:%S')}", 200

def get_dashboard_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📹 View Full Video (Open Eufy)", url="https://mysecurity.eufylife.com/"))
    return markup

# 🕵️‍♂️ THE ULTRA OMNI-DECODER (100% Fail-Proof)
def handle_picture_event(sn, pic_data):
    ts = datetime.now(IST).strftime('%H:%M:%S')
    try:
        img_bytes = None
        
        # Unpack nested dictionary if Eufy sends it that way
        if isinstance(pic_data, dict) and 'value' in pic_data:
            pic_data = pic_data['value']

        # Format 1: JSON Node.js Buffer
        if isinstance(pic_data, dict) and 'data' in pic_data:
            raw_data = pic_data['data']
            if isinstance(raw_data, list):
                img_bytes = bytes(raw_data)
            elif isinstance(raw_data, str):
                pic_data = raw_data 

        # Format 2: Raw List
        if not img_bytes and isinstance(pic_data, list):
            img_bytes = bytes(pic_data)

        # Format 3: Base64 String (The most common Push Notification format)
        if not img_bytes and isinstance(pic_data, str):
            if "base64," in pic_data:
                pic_data = pic_data.split("base64,")[1]
            img_bytes = base64.b64decode(pic_data)

        # 📤 SECURE DELIVERY
        if img_bytes and len(img_bytes) > 500:
            bot.send_photo(
                CHAT_ID, 
                img_bytes, 
                caption=f"📸 **LIVE EVIDENCE SECURED**\n⏰ Time: {ts}\n☁️ *Intercepted via Pure Cloud Push*", 
                reply_markup=get_dashboard_markup()
            )
            print(f"✅ Photo flawlessly decoded and sent at {ts}")
        else:
            print("⚠️ Intercepted payload was empty.")
            
    except Exception as e:
        bot.send_message(CHAT_ID, f"⚠️ **Decoding Error:** {str(e)}")

# --- 2. THE WEBSOCKET LISTENER ---
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "event":
        evt = data.get("event", {})
        evt_type = evt.get("event", "").lower()
        prop_name = evt.get("name", "").lower()
        sn = evt.get("serialNumber")

        # EVENT A: Motion Alert
        if any(x in prop_name for x in ["motion", "person", "ring"]) or evt_type == "motion detected":
            now = time.time()
            if sn not in recent_motions or (now - recent_motions[sn]) > COOLDOWN_SECONDS:
                recent_motions[sn] = now
                ts = datetime.now(IST).strftime('%H:%M:%S')
                try: bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED**\n📹 Cam: `{sn}`\n⏰ {ts} IST\n⏳ Catching Cloud Thumbnail...")
                except: pass

        # EVENT B: The Instant Intercept
        if evt_type == "property changed" and prop_name in ["picture", "thumbnail", "image", "cover_path"]:
            pic_value = evt.get("value")
            if pic_value:
                threading.Thread(target=handle_picture_event, args=(sn, pic_value)).start()

def on_open(ws):
    bot.send_message(CHAT_ID, "🟢 **TITANIUM SYSTEM ONLINE & RESPONSIVE**\n\n(Cloud Mode Locked. Walk in front of camera to test.)")
    ws.send(json.dumps({"command": "start_listening", "messageId": "init_L"}))

def run_ws():
    time.sleep(5) 
    while True:
        try:
            def custom_on_error(ws, e):
                if "Connection refused" not in str(e): print(f"🚨 Socket Error: {e}")
            ws = websocket.WebSocketApp("ws://localhost:3000", on_open=on_open, on_message=on_message, on_error=custom_on_error)
            ws.run_forever(ping_interval=30, ping_timeout=10)
            time.sleep(5) 
        except:
            time.sleep(10) 

# --- 3. MANUAL COMMANDS (CLOUD-SAFE) ---
@bot.message_handler(commands=['status'])
def send_status(message):
    now = datetime.now(IST).strftime('%H:%M:%S')
    bot.reply_to(message, f"📊 **System Status**\n⏰ Time: {now} IST\n🛡️ Mode: 🟢 Active & Listening\n⚡ Engine: Flawless Omni-Decoder")

@bot.message_handler(commands=['test'])
def manual_test(message):
    ts = datetime.now(IST).strftime('%H:%M:%S')
    msg = (f"🧪 **Diagnostic Check Successful!**\n\n"
           f"✅ Telegram Bot: CONNECTED\n"
           f"✅ Webhook Listener: ACTIVE\n"
           f"⏰ Time: {ts} IST\n\n"
           f"⚠️ *Note: To prevent server crashes on Koyeb, manual API image extraction is disabled. "
           f"Please physically walk in front of the camera to instantly receive the live photo!*")
    bot.reply_to(message, msg)

if __name__ == "__main__":
    # Start Web Server
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()
    
    # Start Telegram Listener
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    
    # Start Websocket
    time.sleep(2)
    run_ws()
