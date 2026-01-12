import telebot, os, websocket, json, threading, time, socket
import urllib.request # Media download karne ke liye
from flask import Flask
from datetime import datetime

# --- Config ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# FIX: Driver Port 3000 par chalta hai, 8000 par nahi
WS_URL = "ws://127.0.0.1:3000"
API_URL = "http://127.0.0.1:3000"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Helper ---
def send_msg(text):
    try:
        bot.send_message(CHAT_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"⚠️ TG Error: {e}")

@app.route('/')
def health(): return "Healthy", 200

# --- Status Command ---
@bot.message_handler(commands=['status', 'start'])
def bot_status(message):
    bot.reply_to(message, "✅ **System Online!**\n📹 Connected to Port 3000\n👀 Monitoring Motion")

# --- Motion Alert Logic ---
def send_alert(sn):
    # 1. Text Alert
    timestamp = datetime.now().strftime('%H:%M:%S')
    send_msg(f"🚨 **MOTION DETECTED!**\n📹 Cam: `{sn}`\n⏰ Time: `{timestamp}`")
    
    # 2. Media Sending (Updated Logic: Download first, then send)
    try:
        # Photo
        time.sleep(2)
        url = f"{API_URL}/api/v1/devices/{sn}/last_image"
        # URL se direct download karke Telegram ko bhejein
        with urllib.request.urlopen(url) as response:
            data = response.read()
            bot.send_photo(CHAT_ID, data, caption="📸 Snapshot")
    except Exception as e:
        print(f"❌ Image Error: {e}")

    try:
        # Video
        time.sleep(15) # Video processing time
        url = f"{API_URL}/api/v1/devices/{sn}/last_video"
        with urllib.request.urlopen(url) as response:
            data = response.read()
            bot.send_video(CHAT_ID, data, caption="🎥 Clip")
    except Exception as e:
        print(f"❌ Video Error: {e}")

# --- WebSocket Listener ---
def on_message(ws, message):
    try:
        data = json.loads(message)
        
        # Connection Success
        if data.get("type") == "result" and "devices" in data.get("result", {}):
            count = len(data['result']['devices'])
            send_msg(f"✅ **Connected to Eufy Driver!**\nFound {count} Cameras.")

        # Motion Event
        if data.get("type") == "event" and "event" in data:
            evt = data["event"]
            if "motion" in evt.get("name", "").lower():
                sn = evt.get("serialNumber")
                if sn: threading.Thread(target=send_alert, args=(sn,)).start()
    except: pass

def start_ws():
    print("⏳ Python: Waiting for Driver (Port 3000)...")
    time.sleep(20) 
    
    while True:
        try:
            # FIX: Check Port 3000 (Not 8000)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 3000))
            sock.close()
            
            if result == 0:
                print("🔌 Connecting to Port 3000...")
                ws = websocket.WebSocketApp(WS_URL,
                    on_open=lambda ws: ws.send(json.dumps({"command": "device.get_devices", "messageId": "init"})),
                    on_message=on_message)
                ws.run_forever()
            else:
                print(".", end="", flush=True)
                time.sleep(5)
        except Exception as e:
            print(f"WS Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    send_msg("🚀 **Bot Updated!**\nFixing Port & Media issues...")
    
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
    threading.Thread(target=start_ws, daemon=True).start()
    
    time.sleep(40)
    
    try:
        bot.delete_webhook(drop_pending_updates=True)
        bot.polling(non_stop=True, interval=5)
    except: pass
