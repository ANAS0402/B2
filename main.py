import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
import json
import os

# ===== CONFIG =====
BOT_TOKEN = "8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo"
CHAT_ID = "1873122742"
COINS = ["CFX", "BLUR", "JUP", "MBOX", "PYTH", "PYR", "HMSTR", "ONE"]

bot = Bot(token=BOT_TOKEN)

# Memory for alerts and coin performance
memory_file = "memory.json"
if os.path.exists(memory_file):
    with open(memory_file, "r") as f:
        memory = json.load(f)
else:
    memory = {coin: {"last_alert": 0, "wins": 0, "losses": 0, "bias": 0} for coin in COINS}

# ===== FUNCTIONS =====

def save_memory():
    with open(memory_file, "w") as f:
        json.dump(memory, f)

def get_coin_data(coin):
    """Fetch last 1h data for 1m candles using CoinGecko (free, no key)."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin.lower()}/market_chart?vs_currency=usd&days=1&interval=minute"
    try:
        data = requests.get(url, timeout=10).json()
        prices = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
        volumes = pd.DataFrame(data['total_volumes'], columns=['timestamp', 'volume'])
        df = prices
        df['volume'] = volumes['volume']
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df.tail(60)  # last 60 mins
    except:
        return None

def compute_score(coin, df):
    """Calculate entry score based on anomalies and adaptive memory."""
    if df is None or len(df) < 5:
        return 0, []

    last_price = df['price'].iloc[-1]
    price_change_5m = (last_price - df['price'].iloc[-5]) / df['price'].iloc[-5] * 100
    avg_volume = df['volume'].iloc[:-1].mean()
    last_volume = df['volume'].iloc[-1]
    volume_ratio = last_volume / (avg_volume + 1e-9)

    reasons = []
    score = 0

    # 1. Price spike
    if abs(price_change_5m) > 1:
        score += min(abs(price_change_5m) * 10, 30)
        reasons.append(f"Price move {price_change_5m:.2f}% in 5m")

    # 2. Volume anomaly
    if volume_ratio > 2:
        score += min(volume_ratio * 10, 30)
        reasons.append(f"Volume spike {volume_ratio:.2f}x avg")

    # 3. Whale/fakeout
    if volume_ratio > 3 and abs(price_change_5m) > 2:
        score += 20
        reasons.append("Whale or fakeout pattern detected")

    # 4. Adaptive memory bias
    bias = memory[coin]["bias"]
    score += bias
    if bias > 0:
        reasons.append("Memory bias bullish")
    elif bias < 0:
        reasons.append("Memory bias bearish")

    # 5. Trend check
    trend = df['price'].iloc[-20:].pct_change().mean()
    if trend > 0.001:
        score += 10
        reasons.append("Short-term uptrend detected")
    elif trend < -0.001:
        score += 10
        reasons.append("Short-term downtrend detected")

    return min(score, 100), reasons[:6]  # Limit to 6 reasons

def send_alert(coin, score, reasons):
    """Send a clean Telegram alert with memory info."""
    wins = memory[coin]["wins"]
    losses = memory[coin]["losses"]
    msg = (
        f"🚀 ALIEN ENTRY DETECTED 🚀\n\n"
        f"Coin: {coin}\n"
        f"Score: {score} / 100\n"
        f"Reasons:\n- " + "\n- ".join(reasons) + "\n"
        f"Time (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Memory: Wins={wins} | Losses={losses}"
    )
    bot.send_message(chat_id=CHAT_ID, text=msg)

def scan_market():
    print(f"[{datetime.utcnow()}] Scanning...")
    for coin in COINS:
        df = get_coin_data(coin)
        score, reasons = compute_score(coin, df)

        now = time.time()
        last_time = memory[coin]["last_alert"]

        # Only alert if score >= 80 and 30min passed since last alert
        if score >= 80 and now - last_time > 1800:
            send_alert(coin, score, reasons)
            memory[coin]["last_alert"] = now

            # Adaptive memory: increase bias if triggered
            memory[coin]["bias"] = min(memory[coin]["bias"] + 1, 20)
            save_memory()
        else:
            # Reduce bias slowly to avoid overfitting
            memory[coin]["bias"] = max(memory[coin]["bias"] - 0.1, -10)

# ===== SCHEDULER =====
scheduler = BackgroundScheduler()
scheduler.add_job(scan_market, 'interval', minutes=5)
scheduler.start()

print("🚀 SADDAM B2 Ultra IQ running... Press Ctrl+C to exit.")
while True:
    time.sleep(60)
