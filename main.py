import telebot, os, websocket, json, threading, time, socket
from flask import Flask
from datetime import datetime

# --- Config ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
WS_URL = "ws://127.0.0.1:8000"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Flask Health ---
@app.route('/')
def health(): return "Running", 200

# --- Telegram Helper ---
def send_msg(text):
    try:
        bot.send_message(CHAT_ID, text, parse_mode="Markdown")
    except: pass

# --- Motion Alert ---
def send_alert(sn):
    send_msg(f"🚨 **MOTION!** Cam: `{sn}`")
    try:
        time.sleep(2)
        bot.send_photo(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image")
        time.sleep(15)
        bot.send_video(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_video")
    except: pass

# --- WebSocket ---
def on_message(ws, message):
    try:
        data = json.loads(message)
        if data.get("type") == "result" and "devices" in data.get("result", {}):
            send_msg("✅ **System Online & Connected!**")
        
        if data.get("type") == "event" and "event" in data:
            evt = data["event"]
            if "motion" in evt.get("name", "").lower():
                sn = evt.get("serialNumber")
                if sn: threading.Thread(target=send_alert, args=(sn,)).start()
    except: pass

def start_ws():
    # 30 Second shant rahein taaki Driver ke logs dikhe
    print("⏳ Python Paused: Watching Driver Logs...")
    time.sleep(30)
    
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 8000))
            sock.close()
            
            if result == 0:
                print("🔌 Port 8000 Open! Connecting...")
                ws = websocket.WebSocketApp(WS_URL,
                    on_open=lambda ws: ws.send(json.dumps({"command": "device.get_devices", "messageId": "init"})),
                    on_message=on_message)
                ws.run_forever()
            else:
                # Sirf ek dot (.) print karein taaki spam na ho
                print(".", end="", flush=True) 
                time.sleep(5)
        except:
            time.sleep(10)

if __name__ == "__main__":
    send_msg("🚀 **Bot Restarting...**\nChecking Eufy Login Status...")
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
    threading.Thread(target=start_ws, daemon=True).start()
    
    time.sleep(40) # 409 Fix
    try:
        bot.delete_webhook(drop_pending_updates=True)
        bot.polling(non_stop=True, interval=5)
    except: pass
