
import requests
from textblob import TextBlob
import time

# === CONFIGURATION ===
BOT_TOKEN = "8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo"
CHAT_ID = "1873122742"
COINS = ["CFX", "BLUR", "JUP", "MBOX", "PYTH", "PYR", "HMSTR", "ONE"]
INTERVAL = 60  # check every 60 seconds
ALERT_THRESHOLD = 75  # score threshold for sending alert

def get_price_data(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"
        response = requests.get(url, timeout=10)
        data = response.json()
        return {
            "symbol": symbol,
            "price_change": float(data["priceChangePercent"]),
            "volume": float(data["volume"]),
            "last_price": float(data["lastPrice"])
        }
    except Exception as e:
        return None

def get_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    return "POSITIVE" if polarity > 0.1 else "NEGATIVE"

def fetch_news_placeholder(coin):
    # Placeholder: use mock text
    return [f"{coin} sees increased activity."]

def score_coin(data):
    score = 0
    breakdown = []

    if abs(data["price_change"]) > 5:
        score += 25
        breakdown.append(f"🚀 Strong price change: {data['price_change']}%")

    if data["volume"] > 5000000:
        score += 25
        breakdown.append(f"💸 High volume: {round(data['volume']/1e6, 2)}M")

    news = fetch_news_placeholder(data["symbol"])
    sentiment = get_sentiment(" ".join(news))
    if sentiment == "POSITIVE":
        score += 15
        breakdown.append("🗞️ Positive sentiment (TextBlob)")

    if score >= ALERT_THRESHOLD:
        return score, breakdown
    else:
        return None, None

def send_telegram_alert(symbol, score, breakdown, price):
    message = f"📡 *Entry Alert*: {symbol}USDT\n"               f"📈 Score: *{score}*\n"               f"💰 Price: {price} USDT\n"               + "\n".join(breakdown)
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data=payload)

def run():
    while True:
        for coin in COINS:
            data = get_price_data(coin)
            if data:
                score, breakdown = score_coin(data)
                if score:
                    send_telegram_alert(coin, score, breakdown, data["last_price"])
        time.sleep(INTERVAL)

if __name__ == "__main__":
    run()
