import telebot, os, websocket, json, threading, time, socket
from flask import Flask
from datetime import datetime

# --- Config ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
WS_URL = "ws://127.0.0.1:8000"

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

# --- Status Command (Ab yeh kaam karega) ---
@bot.message_handler(commands=['status', 'start'])
def bot_status(message):
    bot.reply_to(message, "✅ **Bot is Online!**\n👀 Monitoring Motion: 24/7\n📶 Connection: Stable")

# --- Motion Alert Logic ---
def send_alert(sn):
    timestamp = datetime.now().strftime('%H:%M:%S')
    send_msg(f"🚨 **MOTION DETECTED!**\n📹 Cam: `{sn}`\n⏰ Time: `{timestamp}`")
    
    try:
        # Photo
        time.sleep(2)
        bot.send_photo(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image", caption="📸 Snapshot")
        # Video
        time.sleep(15)
        bot.send_video(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_video", caption="🎥 Clip")
    except Exception as e:
        print(f"⚠️ Media Error: {e}")

# --- WebSocket Listener ---
def on_message(ws, message):
    try:
        data = json.loads(message)
        
        # Connection Check
        if data.get("type") == "result" and "devices" in data.get("result", {}):
            send_msg(f"✅ **Connected!** Found {len(data['result']['devices'])} devices.")

        # Motion Event Check (Improved Logic)
        if data.get("type") == "event" and "event" in data:
            evt = data["event"]
            evt_name = evt.get("name", "").lower()
            
            # Debugging: Print event name to logs to see what Eufy is sending
            print(f"🔔 Event Received: {evt_name}")

            # Check for Motion, Person, or Pet detection
            if "motion" in evt_name or "person" in evt_name or "pet" in evt_name:
                sn = evt.get("serialNumber")
                if sn: 
                    print(f"🚨 Triggering Alert for {sn}")
                    threading.Thread(target=send_alert, args=(sn,)).start()
    except: pass

def start_ws():
    print("⏳ Waiting for Driver...")
    time.sleep(20) 
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if sock.connect_ex(('127.0.0.1', 8000)) == 0:
                ws = websocket.WebSocketApp(WS_URL,
                    on_open=lambda ws: ws.send(json.dumps({"command": "device.get_devices", "messageId": "init"})),
                    on_message=on_message)
                ws.run_forever()
            else:
                time.sleep(5)
            sock.close()
        except: time.sleep(10)

if __name__ == "__main__":
    send_msg("🚀 **System Started!**\nUse /status to check connection.")
    
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
    threading.Thread(target=start_ws, daemon=True).start()
    
    time.sleep(40)
    
    try:
        bot.delete_webhook(drop_pending_updates=True)
        bot.polling(non_stop=True, interval=5)
    except Exception as e:
        print(f"Polling Error: {e}")
