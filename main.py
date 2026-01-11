import telebot, os, websocket, json, threading, time
from flask import Flask
from datetime import datetime

# --- Config ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

TESTING_MODE = True 

@app.route('/')
def health(): return "Healthy", 200

# --- Telegram Functions ---
def notify_telegram(msg):
    try:
        bot.send_message(CHAT_ID, f"ℹ️ **System Log:** {msg}", parse_mode="Markdown")
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

@bot.message_handler(commands=['status'])
def status(message):
    bot.reply_to(message, "✅ Bot is active and listening for motion...")

# --- Media Sending Logic ---
def send_alert(sn):
    # Step 1: Pehle Text Alert bhejein (Fastest)
    notify_telegram(f"🚨 **Motion Detected!**\nDevice: {sn}\nTime: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Step 2: Image bhejein
        img_url = f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image"
        bot.send_photo(CHAT_ID, img_url, caption=f"📸 Last Image from {sn}")
        
        # Step 3: Wait for video processing then send
        time.sleep(15) 
        video_url = f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_video"
        bot.send_video(CHAT_ID, video_url, caption=f"🎥 Event Video")
    except Exception as e:
        notify_telegram(f"⚠️ Media Error: {str(e)}")

# --- WebSocket Logic ---
def on_open(ws):
    print("✅ Connected to Eufy Driver")
    notify_telegram("✅ WebSocket Connected to Eufy Driver. Monitoring started.")
    # Driver se devices ki list maangein (Check karne ke liye ki camera connect hai ya nahi)
    ws.send(json.dumps({"command": "device.get_devices", "messageId": "check_devices"}))

def on_msg(ws, msg):
    data = json.loads(msg)
    
    # Debug: Print all messages to console to see what's happening
    print(f"Raw Msg: {msg}")

    # 1. Check if it's a motion event
    if "event" in data and "name" in data["event"]:
        event_name = data["event"]["name"]
        if "motion" in event_name.lower() or "person" in event_name.lower():
            sn = data["event"].get("serialNumber")
            if sn:
                threading.Thread(target=send_alert, args=(sn,)).start()

    # 2. Check device connection status (If driver sends it)
    if "result" in data and "devices" in data.get("result", {}):
        devices = data["result"]["devices"]
        if not devices:
            notify_telegram("⚠️ No cameras found! Please check your Eufy Login.")
        else:
            notify_telegram(f"📷 Found {len(devices)} cameras connected.")

def ws_loop():
    print("⏳ Waiting 100s for Driver Login...")
    time.sleep(100)
    while True:
        try:
            ws = websocket.WebSocketApp(
                "ws://127.0.0.1:8000",
                on_open=on_open,
                on_message=on_msg
            )
            ws.run_forever()
        except Exception as e:
            print(f"WS Error: {e}")
            time.sleep(20)

if __name__ == "__main__":
    # Start Notify
    notify_telegram("🚀 Bot is starting on Koyeb...")
    
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    threading.Thread(target=ws_loop, daemon=True).start()
    
    try:
        bot.remove_webhook()
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Polling Error: {e}")
