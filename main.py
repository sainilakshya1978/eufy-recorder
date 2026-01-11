import telebot, os, websocket, json, threading, time
from flask import Flask
from datetime import datetime

# --- Config ---
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
CHAT_ID = os.getenv('CHAT_ID')
app = Flask(__name__)

# Testing: True rakhein taaki har waqt alert aaye
TESTING_MODE = True 

@app.route('/')
def health(): return "Healthy", 200

def send_to_tg(text):
    try:
        bot.send_message(CHAT_ID, text, parse_mode="Markdown")
    except Exception as e: print(f"TG Error: {e}")

@bot.message_handler(commands=['status'])
def status(message):
    bot.reply_to(message, "✅ Bot Status: Online and Waiting for Motion.")

def send_alert(sn):
    # 1. Sabse pehle Confirm Text bhejein
    send_to_tg(f"🚨 **MOTION DETECTED!**\nCamera: `{sn}`\nTime: {datetime.now().strftime('%H:%M:%S')}")
    
    # 2. Image aur Video bhejneh ki koshish karein
    try:
        # Image
        bot.send_photo(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image", caption="📸 Motion Image")
        # Video ke liye thoda intezar (Driver takes time to save video)
        time.sleep(15)
        bot.send_video(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_video", caption="🎥 Motion Video")
    except Exception as e:
        send_to_tg(f"⚠️ Media Upload Failed: {e}\n(Check if camera is online in Eufy App)")

def on_msg(ws, msg):
    data = json.loads(msg)
    # Debug: Console me log dikhayega
    print(f"Driver Data: {msg}")

    # Motion detection logic
    if "event" in data and "name" in data["event"]:
        evt = data["event"]["name"]
        if "motion" in evt.lower() or "person" in evt.lower():
            sn = data["event"].get("serialNumber")
            if sn: threading.Thread(target=send_alert, args=(sn,)).start()

    # Device detection logic (Jab driver connect ho jaye)
    if "result" in data and "devices" in data.get("result", {}):
        devices = data["result"]["devices"]
        dev_names = [d.get("name", "Unknown") for d in devices]
        send_to_tg(f"✅ **Cameras Linked:** {', '.join(dev_names)}")

def ws_loop():
    # Eufy Driver ko login karne ka waqt dein (CPU usage control)
    print("⏳ Waiting for Driver login...")
    time.sleep(90) 
    
    while True:
        try:
            ws = websocket.WebSocketApp(
                "ws://127.0.0.1:8000",
                on_open=lambda ws: (
                    send_to_tg("🔌 WebSocket Connected! Checking for cameras..."),
                    ws.send(json.dumps({"command": "device.get_devices", "messageId": "init"}))
                ),
                on_message=on_msg
            )
            ws.run_forever()
        except: 
            time.sleep(20)

if __name__ == "__main__":
    # 1. Startup message (Pata chal jayega bot chalu ho gaya)
    send_to_tg("🚀 **Bot Started on Koyeb!**\nWaiting for Eufy Driver (90s)...")
    
    # 2. Threads
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    threading.Thread(target=ws_loop, daemon=True).start()
    
    # 3. Telegram Polling (409 Conflict Fix)
    bot.delete_webhook(drop_pending_updates=True)
    bot.polling(none_stop=True)
