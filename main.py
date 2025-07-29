import threading
import time
import requests
from flask import Flask
from telegram import Bot

# === Telegram Config ===
TOKEN = "8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo"
CHAT_ID = "1873122742"
bot = Bot(token=TOKEN)

# === Your Coin Targets ===
COINS = ["CFX", "BLUR", "JUP", "MBOX", "PYTH", "PYR", "HMSTR", "ONE"]

# === Strategy Parameters ===
ALERT_INTERVAL = 300  # Only alert on a coin every 5 minutes
LAST_ALERT = {}

# === Advanced Filtering (example conditions) ===
def is_strong_entry(coin_data):
    price_change = float(coin_data.get("priceChangePercent", 0))
    volume = float(coin_data.get("quoteVolume", 0))

    # Alien-like logic: sudden dump + high volume = sniper interest
    return price_change < -8 and volume > 1_000_000

# === Binance Price Fetcher ===
def fetch_binance_data():
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/24hr")
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print("Binance fetch error:", e)
    return []

# === Sniper Main Logic ===
def sniper_loop():
    while True:
        print("🔄 Scanning...")
        data = fetch_binance_data()
        now = time.time()

        for coin_data in data:
            symbol = coin_data["symbol"]
            if not any(coin in symbol for coin in COINS):
                continue

            if is_strong_entry(coin_data):
                if symbol not in LAST_ALERT or now - LAST_ALERT[symbol] > ALERT_INTERVAL:
                    message = f"🚨 SNIPER ENTRY DETECTED\nCoin: {symbol}\nDrop: {coin_data['priceChangePercent']}%\nVolume: ${float(coin_data['quoteVolume']):,.0f}"
                    bot.send_message(chat_id=CHAT_ID, text=message)
                    LAST_ALERT[symbol] = now
                    print("🔔 Sent:", message)

        time.sleep(30)

# === Flask Web App for Render Free Tier ===
app = Flask(__name__)

@app.route('/')
def index():
    return "🟢 Saddam Sniper Running..."

# === Run bot in separate thread ===
if __name__ == '__main__':
    threading.Thread(target=sniper_loop).start()
    app.run(host="0.0.0.0", port=3000)
