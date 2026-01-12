import telebot, os, websocket, json, threading, time, socket
import urllib.request
from flask import Flask
from datetime import datetime

# --- Config ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# FIX: Port 3000 (Kyunki Logs mein Driver 3000 par chal raha hai)
WS_URL = "ws://127.0.0.1:3000"
API_URL = "http://127.0.0.1:3000"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Helper ---
def send_msg(text):
    try:
        print(f"📤 TG: {text}")
        bot.send_message(CHAT_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"⚠️ TG Error: {e}")

@app.route('/')
def health(): return "Healthy", 200

@bot.message_handler(commands=['status', 'start'])
def status(m):
    bot.reply_to(m, "✅ **System Online!**\n🔌 Listening on Port 3000\n📡 Waiting for events...")

# --- Alert Logic ---
def send_alert(sn, event_type):
    timestamp = datetime.now().strftime('%H:%M:%S')
    send_msg(f"🚨 **{event_type.upper()} DETECTED!**\n📹 Cam: `{sn}`\n⏰ Time: `{timestamp}`")
    
    # Image Download & Send
    try:
        time.sleep(2)
        url = f"{API_URL}/api/v1/devices/{sn}/last_image"
        # Download karke bhejo (No Cloud Fix)
        with urllib.request.urlopen(url) as response:
            data = response.read()
            bot.send_photo(CHAT_ID, data, caption="📸 Snapshot")
    except Exception as e:
        print(f"❌ Image Failed: {e}")

    # Video Download & Send
    try:
        print("🎥 Attempting Video Download (Wait 20s)...")
        time.sleep(20)
        url = f"{API_URL}/api/v1/devices/{sn}/last_video"
        with urllib.request.urlopen(url) as response:
            data = response.read()
            bot.send_video(CHAT_ID, data, caption="🎥 Clip from SD Card")
    except Exception as e:
        print(f"❌ Video Failed: {e}")

# --- WebSocket Listener ---
def on_message(ws, message):
    try:
        data = json.loads(message)
        
        # 1. Debug Print (Ye Logs mein dikhega ki kya aa raha hai)
        # Isse pata chalega ki Eufy signal bhej raha hai ya nahi
        if data.get("type") != "keep-alive":
            print(f"📨 RAW DATA: {str(data)[:200]}...") 

        # 2. Connection Success
        if data.get("type") == "result" and "devices" in data.get("result", {}):
            count = len(data['result']['devices'])
            send_msg(f"✅ **Connected to Driver!**\nFound {count} Cameras.")

        # 3. Event Handling (Motion/Person/Pet/Ring)
        if data.get("type") == "event" and "event" in data:
            evt = data["event"]
            evt_name = evt.get("name", "").lower()
            sn = evt.get("serialNumber")
            
            print(f"🔔 EVENT DETECTED: {evt_name}") # Log mein dikhega

            if sn and ("motion" in evt_name or "person" in evt_name or "pet" in evt_name or "ring" in evt_name):
                threading.Thread(target=send_alert, args=(sn, evt_name)).start()

    except Exception as e:
        print(f"⚠️ JSON Error: {e}")

def on_error(ws, error):
    print(f"❌ WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("❌ WebSocket Closed")

def start_ws():
    print("⏳ Python Waiting for Port 3000...")
    time.sleep(20)
    
    while True:
        try:
            # Check Port 3000
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 3000))
            sock.close()
            
            if result == 0:
                print("🔌 Connecting to Port 3000...")
                ws = websocket.WebSocketApp(WS_URL,
                    on_open=lambda ws: ws.send(json.dumps({"command": "device.get_devices", "messageId": "init"})),
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close)
                ws.run_forever()
            else:
                print(".", end="", flush=True)
                time.sleep(5)
        except Exception as e:
            print(f"Connection Failed: {e}")
            time.sleep(10)

if __name__ == "__main__":
    send_msg("🚀 **Bot Updated (Debug Mode)**\nChecking Port 3000 connection...")
    
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
    threading.Thread(target=start_ws, daemon=True).start()
    
    time.sleep(40)
    
    try:
        bot.delete_webhook(drop_pending_updates=True)
        bot.polling(non_stop=True, interval=5)
    except: pass
