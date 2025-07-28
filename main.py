# ==============================
#   SADDAM SNIPER PHASE 3.5
#   All-in-One Ghost-Level Algo
#   Telegram Elite Alerts Only
# ==============================

import requests
import time
import threading
from flask import Flask

# === BOT SETTINGS ===
BOT_TOKEN = "8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo"
CHAT_ID = "1873122742"
COINS = ["CFXUSDT", "BLURUSDT", "JUPUSDT", "MBOXUSDT", "PYTHUSDT", "PYRUSDT", "HMSTRUSDT", "ONEUSDT"]
API_URL = "https://api.binance.com/api/v3/klines"
INTERVAL = "1m"
LIMIT = 50

# === FLASK ===
app = Flask(__name__)

@app.route("/")
def home():
    return "SADDAM SNIPER PHASE 3.5 IS ACTIVE"

# === ALERT FUNCTION ===
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

# === UTILS ===
def get_klines(symbol):
    try:
        url = f"{API_URL}?symbol={symbol}&interval={INTERVAL}&limit={LIMIT}"
        r = requests.get(url)
        data = r.json()
        return [
            {
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5])
            } for k in data
        ]
    except:
        return []

# === STRATEGY CORE ===
def analyze(klines):
    if len(klines) < 10:
        return 0

    vol_now = klines[-1]["volume"]
    vol_avg = sum(k["volume"] for k in klines[-10:-1]) / 9
    price_now = klines[-1]["close"]
    price_prev = klines[-2]["close"]
    wick_size = klines[-1]["high"] - klines[-1]["low"]

    # === SIGNAL COMPONENTS ===
    price_move = abs(price_now - price_prev) / price_prev
    vol_spike = vol_now > vol_avg * 2
    wick_thin = wick_size / price_now < 0.01

    whale_detected = vol_spike and wick_thin and price_move > 0.01
    human_dumb_move = price_move < 0.003 and vol_now < vol_avg * 0.8

    score = 0
    if vol_spike: score += 1
    if wick_thin: score += 1
    if whale_detected: score += 1
    if not human_dumb_move: score += 1
    if price_now > klines[-5]["close"]: score += 1

    return score * 20  # scale to 100

# === SCANNER ===
def sniper():
    while True:
        for coin in COINS:
            klines = get_klines(coin)
            score = analyze(klines)

            if score >= 80:
                send_telegram(f"\u2705 ENTRY FOUND! {coin}: Score {score}/100")
        time.sleep(20)

# === STARTUP ===
if __name__ == '__main__':
    threading.Thread(target=sniper).start()
    app.run(host="0.0.0.0", port=3000)


if __name__ == "__main__":
    logging.getLogger('werkzeug').disabled = True
    threading.Thread(target=sniper_loop).start()
    app.run(host='0.0.0.0', port=3000)
