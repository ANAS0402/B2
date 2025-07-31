import json, time, threading
import requests
import websocket
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import deque
from textblob import TextBlob

# ========================
# CONFIG
# ========================
BOT_TOKEN = "8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo"
CHAT_ID = "1873122742"
COINS = ["CFXUSDT","BLURUSDT","JUPUSDT","MBOXUSDT","PYTHUSDT","PYRUSDT","HMSTRUSDT","ONEUSDT"]

ALERT_COOLDOWN = 3600  # 1h between same coin alerts
ALERT_SCORE_MIN = 80

last_alerts = {}
alert_memory = {coin: deque(maxlen=20) for coin in COINS}  # memory of last 20 alerts per coin

# ========================
# KEEP ALIVE SERVER
# ========================
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'SADDAM BOT ULTRA IQ 999 is running')

def run_server():
    server = HTTPServer(('0.0.0.0', 10000), KeepAliveHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ========================
# TELEGRAM ALERT FUNCTION
# ========================
def send_alert(coin, score, reasons, confidence):
    msg = (
        f"🚀 ENTRY ALERT: {coin}\n"
        f"Score: {score}/100\n"
        "Reasons:\n" +
        "\n".join([f"{i+1}. {r}" for i, r in enumerate(reasons)]) +
        f"\nConfidence: {confidence}\n"
        f"Time: {datetime.utcnow().strftime('%H:%M:%S UTC')}"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ========================
# SCORING ENGINE + REASONS
# ========================
price_cache = {}
volume_cache = {}

def calculate_score(coin, old_price, new_price, old_vol, new_vol):
    reasons = []
    if old_price == 0: return 0, reasons

    price_change = ((new_price-old_price)/old_price)*100
    volume_change = ((new_vol-old_vol)/max(1,old_vol))*100

    score = 0
    # 1. Price Momentum
    if abs(price_change) > 0.8:
        score += min(abs(price_change*2), 30)
        reasons.append(f"Price momentum {price_change:+.2f}%")

    # 2. Whale Volume Spike
    if volume_change > 50:
        score += min(volume_change/5, 30)
        reasons.append(f"Whale spike +{volume_change:.1f}% vol")

    # 3. Liquidity Trap Reversal
    if abs(price_change)>1.5 and volume_change>100:
        score += 20
        reasons.append("Liquidity trap reversal (long wick)")

    # 4. Trend Memory Influence
    wins = sum(1 for s in alert_memory[coin] if s >= 80)
    losses = len(alert_memory[coin]) - wins
    if wins >= 3:
        score += 10
        reasons.append(f"Trend memory: {wins}/{len(alert_memory[coin])} past alerts good")

    # 5. Fake Sentiment Divergence
    polarity = TextBlob(coin.lower()).sentiment.polarity
    if (price_change>0 and polarity<0) or (price_change<0 and polarity>0):
        score += 10
        reasons.append("Sentiment divergence detected")

    # 6. Volatility/Noise Filter
    if abs(price_change)<0.2 and volume_change<10:
        score = 0
        reasons = ["Move too weak, filtered"]

    return min(int(score),100), reasons

# ========================
# BINANCE WEBSOCKET
# ========================
def on_message(ws, message):
    data = json.loads(message)
    if 's' not in data: return
    coin = data['s']
    price = float(data['c'])
    vol = float(data['v'])

    old_price = price_cache.get(coin, price)
    old_vol = volume_cache.get(coin, vol)

    score, reasons = calculate_score(coin, old_price, price, old_vol, vol)

    price_cache[coin] = price
    volume_cache[coin] = vol

    now = datetime.utcnow()
    if score >= ALERT_SCORE_MIN:
        last_time = last_alerts.get(coin)
        if not last_time or (now - last_time).total_seconds() > ALERT_COOLDOWN:
            confidence = "🚀 Ultra" if score>=90 else "⚡ Medium"
            send_alert(coin, score, reasons, confidence)
            last_alerts[coin] = now
            alert_memory[coin].append(score)

def on_error(ws, error): print("Error:", error)
def on_close(ws, close_status_code, close_msg): print("WebSocket closed, reconnecting...")
def on_open(ws): print("Connected to Binance WebSocket")

if __name__ == "__main__":
    streams = "/".join([f"{c.lower()}@ticker" for c in COINS])
    ws = websocket.WebSocketApp(f"wss://stream.binance.com:9443/stream?streams={streams}",
                                on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
