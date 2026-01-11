import telebot
import requests
import time
import os

# Environment Variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID') # 8553113399

bot = telebot.TeleBot(BOT_TOKEN)

# 1. Keep Alive Logic (Koyeb ko sone se rokne ke liye)
def keep_alive():
    try:
        requests.get("http://localhost:8000/", timeout=5)
    except:
        pass

# 2. Status Command
@bot.message_handler(commands=['status'])
def send_status(message):
    status_text = (
        "✅ System Status\n\n"
        "🕒 Time: " + time.strftime("%H:%M:%S") + "\n"
        "📡 Server: Online (Port 8000)\n"
        "📸 Monitoring: Active (Photo + Video)"
    )
    bot.reply_to(message, status_text)

# 3. Motion Alert Logic (Photo + Video)
# Yahan bridge ke events ko listen karne ka logic aayega
def handle_motion_event(event_data):
    # Pehle turant Photo bheje (Fast)
    bot.send_message(CHAT_ID, "📸 Motion Detected! Processing video...")
    # bot.send_photo(CHAT_ID, image_data) 
    
    # Phir Video Clip process karke bheje (Slight Delay)
    # bot.send_video(CHAT_ID, video_data)

if __name__ == "__main__":
    print("Bot is starting...")
    while True:
        keep_alive() # Har loop mein heartbeat bheje
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            time.sleep(5)
