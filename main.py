import json, time, threading
import requests
import websocket
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

# ========================
# CONFIG
# ========================
BOT_TOKEN = "8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo"
CHAT_ID = "1873122742"
COINS = ["CFXUSDT","BLURUSDT","JUPUSDT","MBOXUSDT","PYTHUSDT","PYRUSDT","HMSTRUSDT","ONEUSDT"]

ALERT_COOLDOWN = 3600  # 1h between same coin alerts
ALERT_SCORE_MIN = 80

last_alerts = {}  # coin -> last timestamp

# ========================
# KEEP ALIVE HTTP SERVER
# ========================
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'SADDAM BOT is running')

def run_server():
    server = HTTPServer(('0.0.0.0', 10000), KeepAliveHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ========================
# TELEGRAM ALERT FUNCTION
# ========================
def send_alert(coin, score, reason, volume_change):
    msg = (
        f"🚀 ENTRY ALERT: {coin}\n"
        f"Score: {score}/100\n"
        f"Reason: {reason}\n"
        f"Volume Δ: {volume_change}%\n"
        f"Confidence: {'🚀 High' if score>=90 else '⚡ Medium'}\n"
        f"Time: {datetime.utcnow().strftime('%H:%M:%S UTC')}"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ========================
# SIMPLE SCORING ENGINE
# ========================
def calculate_score(old_price, new_price, old_vol, new_vol):
    if old_price == 0: return 0
    price_change = ((new_price-old_price)/old_price)*100
    volume_change = ((new_vol-old_vol)/max(1,old_vol))*100
    score = abs(price_change*2) + min(volume_change/5,50)
    reason = []

    if abs(price_change)>1: reason.append("Price momentum")
    if volume_change>50: reason.append("Whale/Volume spike")
    if abs(price_change)>2 and volume_change>100: reason.append("Liquidity trap reversal")

    return int(min(score,100)), ", ".join(reason) or "Normal move", round(volume_change,2)

# ========================
# BINANCE WEBSOCKET
# ========================
price_cache = {}
volume_cache = {}

def on_message(ws, message):
    global last_alerts
    data = json.loads(message)
    if 's' not in data: return
    coin = data['s']
    price = float(data['c'])
    vol = float(data['v'])

    old_price = price_cache.get(coin, price)
    old_vol = volume_cache.get(coin, vol)

    score, reason, vol_change = calculate_score(old_price, price, old_vol, vol)

    price_cache[coin] = price
    volume_cache[coin] = vol

    # Alert conditions
    now = datetime.utcnow()
    if score >= ALERT_SCORE_MIN:
        last_time = last_alerts.get(coin)
        if not last_time or (now - last_time).total_seconds() > ALERT_COOLDOWN:
            send_alert(coin, score, reason, vol_change)
            last_alerts[coin] = now

def on_error(ws, error): print("Error:", error)
def on_close(ws, close_status_code, close_msg): print("WebSocket closed, reconnecting...")
def on_open(ws): print("Connected to Binance WebSocket")

if __name__ == "__main__":
    streams = "/".join([f"{c.lower()}@ticker" for c in COINS])
    ws = websocket.WebSocketApp(f"wss://stream.binance.com:9443/stream?streams={streams}",
                                on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
