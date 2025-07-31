import requests
import time
from datetime import datetime
from telegram import Bot
import statistics

# --- Telegram Setup ---
BOT_TOKEN = '8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo'
CHAT_ID = '1873122742'
bot = Bot(token=BOT_TOKEN)

# --- Coin IDs (CoinGecko) ---
COINS = {
    "CFX": "conflux-token",
    "BLUR": "blur",
    "JUP": "jupiter-exchange",
    "MBOX": "mobox",
    "PYTH": "pyth-network",
    "PYR": "vulcan-forged",
    "HMSTR": "hamster",
    "ONE": "harmony"
}

# --- Memory to Avoid Repeated Alerts ---
last_scores = {}

# --- RSI Calculation (lightweight, custom) ---
def compute_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    gains = [max(prices[i] - prices[i-1], 0) for i in range(1, len(prices))]
    losses = [max(prices[i-1] - prices[i], 0) for i in range(1, len(prices))]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# --- Get historical prices (24h sparkline) ---
def get_historical_prices(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&sparkline=true"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            prices = res.json()["market_data"]["sparkline_7d"]["price"][-100:]  # Last ~24h
            return prices
        return []
    except:
        return []

# --- Get current coin data ---
def fetch_coin_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            return {
                "price": data["market_data"]["current_price"]["usd"],
                "volume": data["market_data"]["total_volume"]["usd"],
                "change_24h": data["market_data"]["price_change_percentage_24h"],
                "sparkline": data["market_data"]["sparkline_7d"]["price"][-100:]
            }
        return None
    except:
        return None

# --- Scoring Logic with Pattern Recognition ---
def score_coin(data):
    if not data: return 0
    score = 0

    # Price Change
    if data["change_24h"] > 3:
        score += 25
    elif data["change_24h"] > 1:
        score += 10

    # Volume Boost
    if data["volume"] > 5_000_000:
        score += 25
    elif data["volume"] > 1_000_000:
        score += 10

    # RSI
    rsi = compute_rsi(data["sparkline"])
    if rsi and rsi < 30:
        score += 30  # oversold
    elif rsi and 30 <= rsi <= 70:
        score += 10

    # Trend check: upward trend in sparkline
    if data["sparkline"][-1] > statistics.mean(data["sparkline"][-10:]):
        score += 10

    return score, rsi

# --- Alert Message Constructor ---
def build_alert(symbol, score, data, rsi):
    return f"""
🚨 *SADDAM ENTRY ALERT* 🚨

*Coin:* {symbol}
*Price:* ${data['price']:.4f}
*Change (24h):* {data['change_24h']:.2f}%
*Volume:* ${data['volume']:,.0f}
*RSI:* {rsi:.2f}
*Score:* {score}/100

🧠 Analysis:
- Price momentum: ✅
- Volume strength: ✅
- RSI-based pattern: ✅
- Trend confirmation: ✅

🔁 Powered by Saddam (mirrored from Aladdin)
"""

# --- Main Analysis Loop ---
def analyze_market():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Running full scan...")
    for symbol, coin_id in COINS.items():
        data = fetch_coin_data(coin_id)
        if not data:
            continue
        score, rsi = score_coin(data)
        if score >= 80 and last_scores.get(symbol) != score:
            last_scores[symbol] = score
            message = build_alert(symbol, score, data, rsi)
            bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

# --- Scheduled Loop ---
def main():
    while True:
        analyze_market()
        time.sleep(300)

if __name__ == "__main__":
    main()
