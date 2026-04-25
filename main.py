import telebot, os, websocket, json, threading, time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from datetime import datetime
import pytz

# --- 1. SYSTEM CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 
IST = pytz.timezone('Asia/Kolkata')

print("⚡ Initializing Titanium Event-Driven Engine (Ultra Way)...")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Prevent spamming alerts
recent_motions = {}
COOLDOWN_SECONDS = 30 

@app.route('/')
def health():
    return f"Titanium Event Engine Online | Time: {datetime.now(IST).strftime('%H:%M:%S')}", 200

def get_dashboard_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📹 View Full Video (Open Eufy)", url="https://mysecurity.eufylife.com/"))
    return markup

# 🕵️‍♂️ THE INSTANT INTERCEPTOR
def handle_picture_event(sn, pic_data):
    """Fires the millisecond the picture arrives on the websocket"""
    ts = datetime.now(IST).strftime('%H:%M:%S')
    try:
        img_bytes = None
        # Extract the Node.js Buffer array
        if isinstance(pic_data, dict) and 'data' in pic_data:
            img_bytes = bytes(pic_data['data'])
        elif isinstance(pic_data, list):
            img_bytes = bytes(pic_data)
        
        if img_bytes and len(img_bytes) > 1000:
            bot.send_photo(
                CHAT_ID, 
                img_bytes, 
                caption=f"📸 **EVIDENCE SECURED**\n⏰ Time: {ts}\n💾 *Video is on Camera SD Card.*", 
                reply_markup=get_dashboard_markup()
            )
            print(f"✅ Intercepted and sent photo successfully at {ts}")
    except Exception as e:
        bot.send_message(CHAT_ID, f"⚠️ Error processing intercepted photo: {e}")

# --- 2. THE WEBSOCKET LISTENER ---
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "event":
        evt = data.get("event", {})
        evt_type = evt.get("event", "").lower()
        prop_name = evt.get("name", "").lower()
        sn = evt.get("serialNumber")

        # ACTION 1: Motion Detected
        if any(x in prop_name for x in ["motion", "person", "ring"]) or evt_type == "motion detected":
            now = time.time()
            if sn not in recent_motions or (now - recent_motions[sn]) > COOLDOWN_SECONDS:
                recent_motions[sn] = now
                ts = datetime.now(IST).strftime('%H:%M:%S')
                try: 
                    bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED**\n📹 Cam: `{sn}`\n⏰ {ts} IST\n⏳ Awaiting instantaneous Push payload...")
                except: pass

        # ACTION 2: The "Ultra Way" Photo Intercept
        # We listen directly for the property change, bypassing the REST API entirely.
        if evt_type == "property changed" and prop_name in ["picture", "thumbnail", "image"]:
            pic_value = evt.get("value")
            if pic_value:
                # Send the processing to a background thread so we don't block the socket
                threading.Thread(target=handle_picture_event, args=(sn, pic_value)).start()

def on_open(ws):
    bot.send_message(CHAT_ID, "🟢 **TITANIUM SYSTEM ONLINE (Ultra Event-Driven Edition)**")
    ws.send(json.dumps({"command": "start_listening", "messageId": "init_L"}))

def run_ws():
    time.sleep(5) 
    while True:
        try:
            def custom_on_error(ws, e):
                if "Connection refused" not in str(e): print(f"🚨 Error: {e}")

            ws = websocket.WebSocketApp("ws://localhost:3000", on_open=on_open, on_message=on_message, on_error=custom_on_error)
            ws.run_forever(ping_interval=30, ping_timeout=10)
            time.sleep(5) 
        except:
            time.sleep(10) 

# --- 3. MANUAL COMMANDS ---
@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, f"📊 **System Status**\n🛡️ Mode: 🟢 Active\n⚡ Engine: Event-Driven Push Interceptor")

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    time.sleep(2)
    run_ws()
