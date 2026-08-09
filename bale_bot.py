import os
import requests
import time

TOKEN = os.getenv("BALE_BOT_TOKEN")

URL = f"https://tapi.bale.ai/bot{TOKEN}/getUpdates"

print("=== BALE BOT TEST ===")
print("Token exists:", bool(TOKEN))
print("Testing connection...")

while True:
    try:
        response = requests.get(
            URL,
            timeout=30
        )

        print("HTTP STATUS:", response.status_code)
        print("RESPONSE:", response.text)

    except Exception as e:
        print("ERROR:", e)

    time.sleep(10)
