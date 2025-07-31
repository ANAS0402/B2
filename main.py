import requests, json, time, os, random
from datetime import datetime
from textblob import TextBlob
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot

BOT_TOKEN = "8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo"
CHAT_ID = "1873122742"
COINS = ["CFX", "BLUR", "JUP", "MBOX", "PYTH", "PYR", "HMSTR", "ONE"]
MEMORY_FILE = "memory.json"
SCORE_THRESHOLD = 85

bot = Bot(token=BOT_TOKEN)

if not os.path.exists(MEMORY_FILE):
    json.dump({"alerts": {}, "success": {}}, open(MEMORY_FILE, "w"))

def load_memory():
    return json.load(open(MEMORY_FILE))

def save_memory(mem):
    json.dump(mem, open(MEMORY_FILE, "w"))

def fetch_price(coin):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "ids": coin.lower()}
    try:
        data = requests.get(url, params=params, timeout=5).json()
        if data:
            return {
                "price": data[0]["current_price"],
                "volume": data[0]["total_volume"],
                "change_1h": data[0].get("price_change_percentage_1h_in_currency", 0)
            }
    except:
        return None
    return None

def alien_prediction(coin, price_info):
    """
    Alien logic: simulate multiple futures with randomness to find hidden moves.
    """
    if not price_info: return 0, "No data"
    # Monte Carlo style prediction
    projections = [price_info["price"] * (1 + random.uniform(-0.02,0.03)) for _ in range(30)]
    upward_bias = sum(1 for p in projections if p > price_info["price"]) / len(projections)
    reason = f"Alien projection shows {upward_bias*100:.0f}% bullish micro-future"
    return upward_bias*100, reason

def compute_score(coin, price_info, memory):
    if not price_info: return 0, []

    score = 0
    reasons = []

    # 1. Volume & price momentum
    if abs(price_info["change_1h"]) > 1:
        score += 20
        reasons.append(f"Momentum {price_info['change_1h']:.2f}%")

    if price_info["volume"] > 1_000_000:
        score += 20
        reasons.append(f"Whale volume {price_info['volume']:,}")

    # 2. Sentiment twist
    sent = TextBlob(f"{coin} crypto market hype").sentiment.polarity*100
    if (sent>30 and price_info["change_1h"]<0) or (sent< -30 and price_info["change_1h"]>0):
        score += 15
        reasons.append(f"Sentiment divergence {sent:.1f}")

    # 3. Alien prediction
    alien_score, alien_reason = alien_prediction(coin, price_info)
    if alien_score>50:
        score += 25
        reasons.append(alien_reason)

    # 4. Memory boost
    success_rate = memory["success"].get(coin, 50)
    if success_rate>60:
        score+=10
        reasons.append(f"Memory favor: {success_rate}% accuracy")

    return min(score,100), reasons

def send_alert(coin, score, reasons):
    msg = f"👽 ALIEN ENTRY: {coin}\nScore {score}/100\nReasons:\n"
    msg += "\n".join([f"• {r}" for r in reasons])
    msg += f"\nTime: {datetime.utcnow()} UTC"
    bot.send_message(chat_id=CHAT_ID, text=msg)

def scan_market():
    mem = load_memory()
    for coin in COINS:
        info = fetch_price(coin)
        score, reasons = compute_score(coin, info, mem)
        if score < SCORE_THRESHOLD or len(reasons)<3:
            continue

        last_alerts = mem["alerts"].get(coin,[])
        now = time.time()
        if last_alerts and now - last_alerts[-1] < 3600:
            continue

        mem["alerts"].setdefault(coin,[]).append(now)
        mem["alerts"][coin] = mem["alerts"][coin][-10:]
        save_memory(mem)

        send_alert(coin,score,reasons)

sched = BackgroundScheduler()
sched.add_job(scan_market,"interval",minutes=2)
sched.start()
print("👽 SADDAM Alien IQ∞ running...")
while True:
    time.sleep(60)
