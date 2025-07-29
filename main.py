import time
import requests
from telegram import Bot

# === CONFIG ===
BOT_TOKEN = "8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo"
CHAT_ID = "1873122742"
SYMBOLS = ["CFX", "BLUR", "JUP", "MBOX", "PYTH", "PYR", "HMSTR", "ONE"]
MIN_SCORE_TO_ALERT = 85
CHECK_INTERVAL = 60  # seconds
bot = Bot(token=BOT_TOKEN)

def fetch_klines(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1m&limit=10"
    response = requests.get(url)
    return response.json()

def analyze(symbol):
    klines = fetch_klines(symbol)
    if len(klines) < 10:
        return None

    last = klines[-1]
    close = float(last[4])
    high = float(last[2])
    low = float(last[3])
    open_ = float(last[1])
    volume = float(last[5])
    
    wick_down = open_ - low if open_ > low else 0
    wick_up = high - close if close < high else 0
    body = abs(close - open_)

    # Score system
    score = 0
    reason = []

    # 1. Wick detection (liquidity grab)
    if wick_down > body * 2:
        score += 30
        reason.append("Long wick down (liquidity grab)")

    # 2. Volume spike
    volumes = [float(k[5]) for k in klines[:-1]]
    avg_volume = sum(volumes[-5:]) / 5
    if volume > avg_volume * 2:
        score += 25
        reason.append("Volume spike")

    # 3. Volatility squeeze breakout
    closes = [float(k[4]) for k in klines[-6:]]
    volatility = max(closes) - min(closes)
    if volatility / close < 0.005:  # <0.5%
        score -= 20  # compressing
    elif volatility / close > 0.015:
        score += 20
        reason.append("Volatility breakout")

    # 4. Price recovery (close > open after big wick)
    if wick_down > 0 and close > open_:
        score += 15
        reason.append("Price recovery after wick")

    # 5. Momentum: higher high
    prev_high = float(klines[-2][2])
    if high > prev_high:
        score += 10
        reason.append("Higher high formed")

    return {
        "symbol": symbol,
        "score": score,
        "price": close,
        "reason": reason
    }

def send_alert(data):
    msg = f"🚨 ENTRY SIGNAL [{data['symbol']}]\n"
    msg += f"Price: {data['price']:.4f} USDT\n"
    msg += f"Score: {data['score']} / 100\n"
    msg += "Reasons:\n"
    for r in data["reason"]:
        msg += f"• {r}\n"
    bot.send_message(chat_id=CHAT_ID, text=msg)

def main_loop():
    print("🧠 Sniper Phase 3 started...")
    while True:
        for sym in SYMBOLS:
            try:
                data = analyze(sym)
                if data and data['score'] >= MIN_SCORE_TO_ALERT:
                    send_alert(data)
            except Exception as e:
                print(f"Error on {sym}: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
