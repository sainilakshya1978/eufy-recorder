import telebot, os, websocket, json, threading, time, requests
from flask import Flask
from datetime import datetime
import pytz

# --- Config ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
IST = pytz.timezone('Asia/Kolkata')

# Using Localhost for high speed internal communication
WS_URL = "ws://127.0.0.1:3000"
API_URL = "http://127.0.0.1:3000"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

def send_tg_log(text):
    try:
        bot.send_message(CHAT_ID, f"ℹ️ **System Log:**\n{text}", parse_mode="Markdown")
    except: pass

@app.route('/')
def health(): return "Bot is Alive", 200

# --- Status Command ---
@bot.message_handler(commands=['status', 'start'])
def status(m):
    now = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
    bot.reply_to(m, f"✅ **Cloud Deployment Status:**\n\n🟢 **Instance:** Healthy\n🔌 **Driver:** Running (Port 3000)\n⏰ **Server Time:** {now}\n🛡️ **Security:** Armed")

# --- Alert Logic ---
def send_alert(sn, event):
    now = datetime.now(IST).strftime('%H:%M')
    # Initial Text Alert
    bot.send_message(CHAT_ID, f"🚨 **MOTION DETECTED**\n📸 Camera: `{sn}`\n⏰ Time: `{now} IST`")
    
    # Try to fetch Image
    try:
        time.sleep(3)
        img_res = requests.get(f"{API_URL}/api/v1/devices/{sn}/last_image", timeout=10)
        if img_res.status_code == 200:
            bot.send_photo(CHAT_ID, img_res.content, caption=f"📸 Snapshot from {sn}")
    except: pass

# --- WebSocket Engine ---
def on_message(ws, message):
    data = json.loads(message)
    # Check for device events
    if data.get("type") == "event":
        evt = data.get("event", {})
        if any(x in evt.get("name", "").lower() for x in ["motion", "person", "ring"]):
            sn = evt.get("serialNumber")
            threading.Thread(target=send_alert, args=(sn, evt.get("name"))).start()
    
    # Check for successful device discovery
    elif "devices" in data.get("result", {}):
        count = len(data['result']['devices'])
        send_tg_log(f"✅ **Driver Synced!**\nFound {count} cameras online.")

def on_open(ws):
    print("Socket Connected")
    ws.send(json.dumps({"command": "start_listening", "messageId": "start"}))
    ws.send(json.dumps({"command": "device.get_devices", "messageId": "init"}))

def run_ws():
    while True:
        try:
            ws = websocket.WebSocketApp(WS_URL, on_open=on_open, on_message=on_message)
            ws.run_forever()
        except: pass
        time.sleep(10)

if __name__ == "__main__":
    # 1. Start Flask Health Check
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    
    # 2. Wait and Start WebSocket
    time.sleep(5) 
    threading.Thread(target=run_ws, daemon=True).start()
    
    # 3. Notify Telegram that deployment is finished
    send_tg_log("🚀 **Cloud Deployment Successful!**\nAll systems are now monitoring.")
    
    # 4. Start Telegram Bot
    bot.polling(none_stop=True)
