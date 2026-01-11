import telebot
import os
import websocket
import json
import time

# 1. Configuration - Koyeb Variables se data uthayega
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telebot.TeleBot(BOT_TOKEN)

def handle_motion(device_sn):
    print(f"🚨 ALERT: Motion detected on device {device_sn}")
    try:
        # Step 1: Send Photo
        img_url = f"http://127.0.0.1:8000/api/v1/devices/{device_sn}/last_image"
        bot.send_photo(CHAT_ID, img_url, caption=f"🚨 Motion Detected!\nDevice: {device_sn}")
        
        # Step 2: Wait for video to process (15 seconds recommended for cloud)
        print("⏳ Waiting for video clip...")
        time.sleep(15)
        
        # Step 3: Send Video
        video_url = f"http://127.0.0.1:8000/api/v1/devices/{device_sn}/last_video"
        bot.send_video(CHAT_ID, video_url, caption="🎥 Video Clip")
        print("✅ Media sent successfully!")
    except Exception as e:
        print(f"❌ Media Error: {e}")

def on_message(ws, message):
    data = json.loads(message)
    # Check if the event is motion or person detection
    msg_str = str(data).lower()
    if data.get("type") == "event" and ("motion" in msg_str or "person" in msg_str):
        device_sn = data.get("metadata", {}).get("serial_number")
        if device_sn:
            handle_motion(device_sn)

def start_bot():
    # Eufy Driver ko login ke liye poora 1 minute dena zaroori hai
    print("⏳ System initializing... Waiting 60s for Driver login...")
    time.sleep(60) 
    
    while True:
        try:
            print("🔗 Attempting to connect to Eufy Bridge...")
            ws = websocket.WebSocketApp(
                "ws://127.0.0.1:8000",
                on_message=on_message,
                on_open=lambda ws: print("✅ SUCCESS: Connected to Eufy Camera Server!"),
                on_error=lambda ws, e: print(f"⚠️ Connection Error: {e}")
            )
            ws.run_forever()
        except Exception as e:
            print(f"❌ Connection lost. Retrying in 10s... {e}")
            time.sleep(10)

if __name__ == "__main__":
    print("🤖 Eufy Telegram Bot is starting in Worker Mode...")
    start_bot()
