import telebot, os, websocket, json, threading, time
from flask import Flask
from datetime import datetime

# --- Configuration ---
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
CHAT_ID = os.getenv('CHAT_ID')
app = Flask(__name__)

# TESTING_MODE: 
# True = Abhi alerts aayenge (Testing ke liye)
# False = Sirf Raat 12 se Subah 5 tak aayenge (Final use ke liye)
TESTING_MODE = True 

START_H = 0  # Raat ke 12 baje (00:00)
END_H = 5    # Subah ke 5 baje (05:00)

@app.route('/')
def health(): return "System Online", 200

# --- Telegram Status Command ---
@bot.message_handler(commands=['status'])
def status(message):
    now = datetime.now().hour
    mode = "TESTING (Alerts Always On)" if TESTING_MODE else "LIVE (Raat 12-5 Only)"
    status_text = (
        f"✅ Bot Status: Active\n"
        f"⏰ Alert Window: 00:00 - 05:00\n"
        f"⌚ Current Hour: {now}:00\n"
        f"⚙️ Mode: {mode}"
    )
    bot.reply_to(message, status_text)

# --- Media Sending Logic ---
def send_alert(sn):
    now = datetime.now().hour
    # Condition: Agar Testing ON hai YA raat ke 12 se subah 5 ka waqt hai
    if TESTING_MODE or (START_H <= now < END_H):
        try:
            print(f"🚨 ALERT TRIGGERED: Motion at {now}:00 for {sn}")
            # Step 1: Photo
            bot.send_photo(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_image", 
                           caption=f"🚨 Raat ka Alert! Motion Detected at {datetime.now().strftime('%H:%M')}")
            
            # Step 2: Buffer for Video (20 seconds recommended)
            time.sleep(20) 
            
            # Step 3: Video
            bot.send_video(CHAT_ID, f"http://127.0.0.1:8000/api/v1/devices/{sn}/last_video", caption="🎥 Incident Clip")
        except Exception as e: 
            print(f"❌ Media Error: {e}")
    else:
        print(f"😴 Daytime Mode: Outside 00:00-05:00 window. Alert skipped.")

# --- WebSocket Driver Connection ---
def on_msg(ws, msg):
    data = json.loads(msg)
    # Event check for motion
    if "motion" in str(data).lower() or "person" in str(data).lower():
        sn = data.get("metadata", {}).get("serial_number")
        if sn: 
            threading.Thread(target=send_alert, args=(sn,)).start()

def ws_loop():
    print("⏳ System initializing... Waiting 60s for Driver Login...")
    time.sleep(60) 
    while True:
        try:
            print("🔗 Connecting to Eufy Bridge on Port 8000...")
            ws = websocket.WebSocketApp("ws://127.0.0.1:8000", 
                                        on_message=on_msg,
                                        on_open=lambda ws: print("✅ SUCCESS: Connected to Camera Server!"))
            ws.run_forever()
        except: 
            print("⚠️ Connection lost, retrying in 10s...")
            time.sleep(10)

if __name__ == "__main__":
    # Flask Health Check for Koyeb
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    
    # Eufy WebSocket Thread
    threading.Thread(target=ws_loop, daemon=True).start()
    
    # Telegram Bot
    print("🤖 Telegram Bot Polling Started...")
    bot.remove_webhook()
    bot.polling(none_stop=True)
