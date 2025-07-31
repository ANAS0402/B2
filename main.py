import time
import requests
import pandas as pd
import numpy as np
import random
from datetime import datetime
from collections import deque
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Bot

# === CONFIG ===
BOT_TOKEN = "8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo"
CHAT_ID = "1873122742"
COINS = ["CFX", "BLUR", "JUP", "MBOX", "PYTH", "PYR", "HMSTR", "ONE"]

bot = Bot(token=BOT_TOKEN)

# Memory
alert_memory = deque(maxlen=10)
coin_memory = {coin: {"wins": 0, "losses": 0, "last_score": 50} for coin in COINS}

# === Lightweight Price Fetch (Binance free API) ===
def get_price_volume(coin):
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={coin}USDT"
    try:
        data = requests.get(url, timeout=5).json()
        price = float(data['lastPrice'])
        vol = float(data['volume'])
        return price, vol
    except:
        return None, None

# === Alien IQ Scoring ===
def score_coin(coin):
    price, volume = get_price_volume(coin)
    if price is None: 
        return None

    # Random "alien insight" factor to mimic whales & market traps
    whale_factor = random.uniform(0.8, 1.2)
    
    # Simple volatility metric
    vol_score = min(volume / 1000, 100)

    # Historical bias memory
    bias = coin_memory[coin]["last_score"]
    
    # Final evolving score
    score = (whale_factor * vol_score + random.uniform(0, 50) + bias * 0.3)
    score = min(score, 100)

    # Self-learn: adjust bias
    if score > 85:
        coin_memory[coin]["wins"] += 1
    else:
        coin_memory[coin]["losses"] += 1
    coin_memory[coin]["last_score"] = score

    # Reasons for alert
    reasons = [
        f"Volume spike: {round(vol_score,2)}",
        f"Whale factor: {round(whale_factor,2)}",
        f"Adaptive memory bias: {round(bias,2)}"
    ]
    return score, reasons

# === Telegram alert ===
def send_alert(coin, score, reasons):
    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    message = (
        f"🚀 ALIEN ENTRY DETECTED 🚀\n\n"
        f"Coin: {coin}\n"
        f"Score: {round(score,2)} / 100\n"
        f"Reasons:\n- " + "\n- ".join(reasons) + "\n"
        f"Time (UTC): {ts}\n"
        f"Memory: Wins={coin_memory[coin]['wins']} | Losses={coin_memory[coin]['losses']}"
    )
    bot.send_message(chat_id=CHAT_ID, text=message)

# === Scanner Loop ===
def scan_loop():
    while True:
        for coin in COINS:
            result = score_coin(coin)
            if result:
                score, reasons = result
                alert_key = f"{coin}-{int(score)}"
                if score >= 85 and alert_key not in alert_memory:
                    alert_memory.append(alert_key)
                    send_alert(coin, score, reasons)
        time.sleep(30)  # scans every 30s

# === Keep Alive Server ===
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'SADDAM Alien IQ9999999 is running')

def run_server():
    server = HTTPServer(('0.0.0.0', 10000), KeepAliveHandler)
    server.serve_forever()

threading.Thread(target=run_server).start()

if __name__ == "__main__":
    scan_loop()
