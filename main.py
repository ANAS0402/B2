# Saddam System - Final Alladin Mirror (Light Version for Free Tier)

import requests
import time
import yfinance as yf
import schedule
from textblob import TextBlob
from telegram import Bot
import pandas as pd

# === CONFIGURATION ===
BOT_TOKEN = "8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo"
CHAT_ID = "1873122742"
COINS = ["CFX", "BLUR", "JUP", "MBOX", "PYTH", "PYR", "HMSTR", "ONE"]
SLEEP_INTERVAL = 60 * 5  # Every 5 minutes
SCORE_THRESHOLD = 80
ALERT_MEMORY = {}

bot = Bot(token=BOT_TOKEN)

# === FUNCTIONS ===

def fetch_coin_data(coin):
    try:
        df = yf.download(f"{coin}-USDT", period="1d", interval="5m")
        if len(df) < 2:
            return None
        return df
    except:
        return None

def analyze_sentiment(coin):
    try:
        url = f"https://news.google.com/rss/search?q={coin}+crypto"
        response = requests.get(url)
        blob = TextBlob(response.text)
        return blob.sentiment.polarity * 100  # scale -100 to +100
    except:
        return 0

def score_signal(df, sentiment_score):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Features
    price_change = ((last['Close'] - prev['Close']) / prev['Close']) * 100
    volume_spike = (last['Volume'] / df['Volume'].mean())

    score = 0
    explanation = []

    if abs(price_change) > 2:
        score += 20
        explanation.append(f"Price change: {price_change:.2f}%")

    if volume_spike > 2:
        score += 25
        explanation.append(f"Volume spike: {volume_spike:.2f}x")

    if sentiment_score > 20 or sentiment_score < -20:
        score += 20
        explanation.append(f"Sentiment: {sentiment_score:.2f}")

    # Behavioral adjustment
    if coin in ALERT_MEMORY and ALERT_MEMORY[coin]['last_result'] == 'fail':
        score -= 15
        explanation.append("Lowered score due to past bad alert")

    return min(score, 100), explanation

def send_telegram_alert(coin, score, explanation):
    emojis = "🚀" if score > 90 else "⚠️" if score >= 80 else "🐌"
    if coin in ALERT_MEMORY and time.time() - ALERT_MEMORY[coin]['last_time'] < 3600:
        return  # skip repeat alerts within 1 hour

    message = f"\n🔥 ENTRY DETECTED - {coin} {emojis}\n"
    message += f"Confidence Score: {score}/100\n"
    message += "\n".join(explanation)

    bot.send_message(chat_id=CHAT_ID, text=message)
    ALERT_MEMORY[coin] = {"last_time": time.time(), "last_result": 'sent'}

def monitor():
    print("Scanning...")
    for coin in COINS:
        df = fetch_coin_data(coin)
        if df is None:
            continue

        sentiment = analyze_sentiment(coin)
        score, explanation = score_signal(df, sentiment)

        if score >= SCORE_THRESHOLD:
            send_telegram_alert(coin, score, explanation)

# === MAIN LOOP ===
schedule.every(SLEEP_INTERVAL).seconds.do(monitor)

print("SADDAM system live...")
monitor()  # run first manually

while True:
    schedule.run_pending()
    time.sleep(5)
