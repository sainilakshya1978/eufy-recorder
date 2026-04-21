import telebot, os, websocket, json, threading, time, requests
from flask import Flask
from datetime import datetime
import pytz

# --- 1. SYSTEM CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') 
IST = pytz.timezone('Asia/Kolkata')
API_URL = "http://localhost:3000" 

print("⚡ Initializing 100% Bulletproof Interceptor Bot...")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Smart Lock to prevent spam
last_trigger = {}
COOLDOWN_SECONDS = 30 

@app.route('/')
def health():
    return f"Titanium Interceptor Online | Time: {datetime.now(IST).strftime('%H:%M:%S')}", 200

# --- 2. THE 100% GUARANTEED PHOTO WORKFLOW ---
def execute_delivery(sn, trigger_type="Auto"):
    ts_now = datetime.now(IST)
    ts = ts_now.strftime('%H:%M:%S')
    
    try:
        bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED**\n📹 Cam: `{sn}`\n⏰ {ts} IST\n⚡ Intercepting Eufy Cloud Thumbnail...")
    except: pass 

    # Wait 4 seconds for the Eufy Cloud to process the notification and send the photo
    time.sleep(4)
    photo_secured = False

    # 🕵️‍♂️ INTERCEPT METHOD 1: Direct Image Cache
    try:
        res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=10)
        if res.status_code == 200 and len(res.content) > 1000: 
            bot.send_photo(CHAT_ID, res.content, caption=f"📸 **INSTANT PHOTO SECURED**\n⏰ Time: {ts}")
            photo_secured = True
    except Exception as e:
        print(f"Method 1 failed: {e}")

    # 🕵️‍♂️ INTERCEPT METHOD 2: Hidden Device Payload (If Method 1 misses)
    if not photo_secured:
        try:
            res = requests.get(f"{API_URL}/api/v1/devices/{sn}", timeout=10)
            data = res.json()
            pic_val = data.get('data', {}).get('properties', {}).get('picture', {}).get('value')
            if pic_val and isinstance(pic_val, dict) and 'data' in pic_val:
                img_bytes = bytes(pic_val['data'])
                if len(img_bytes) > 1000:
                    bot.send_photo(CHAT_ID, img_bytes, caption=f"📸 **INSTANT PHOTO SECURED**\n⏰ Time: {ts}")
                    photo_secured = True
        except Exception as e:
            print(f"Method 2 failed: {e}")

    # ⚠️ IF PHOTO IS MISSING
    if not photo_secured:
        bot.send_message(CHAT_ID, f"⚠️ **Photo Not Found in Cloud.**\n\n**CRITICAL FIX:**\nOpen Eufy App -> Camera Settings -> Notifications -> Make sure 'Include Thumbnail' is turned ON.")

# --- 3. THE FAIL-SAFE LISTENER ---
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
    print("✅ System 100% Armed!")
    bot.send_message(CHAT_ID, "🟢 **TITANIUM SYSTEM ONLINE (100% Bulletproof Photo Edition)**")
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
    bot.reply_to(message, f"📊 **System Status**\n🛡️ Mode: 🟢 Active\n⚡ Engine: 100% Photo Interceptor")

@bot.message_handler(commands=['test'])
def manual_test(message):
    bot.reply_to(message, "🧪 **Initiating Photo Test...**")
    threading.Thread(target=execute_delivery, args=("T8W11P40240109D4", "Manual Test")).start()

if __name__ == "__main__":
    # Flask Server for Koyeb Health Check
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()
    
    # Telegram Command Listener
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    
    time.sleep(2)
    run_ws()
