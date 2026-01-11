import time
import requests

def keep_alive():
    try:
        # Yeh line Koyeb ko batati hai ki app active hai
        requests.get("http://localhost:8000/", timeout=5)
    except:
        pass

# Aapki main loop mein ise har 30 seconds mein chalayein
while True:
    keep_alive()
    time.sleep(30)
