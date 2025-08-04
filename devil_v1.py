import os
import sqlite3
import ccxt
import datetime
import time
import random
from telegram import Bot

# Telegram Config
TELEGRAM_TOKEN = "8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo"
CHAT_ID = "1873122742"

bot = Bot(token=TELEGRAM_TOKEN)

WATCHLIST = ["CFX/USDT", "BLUR/USDT", "JUP/USDT", "MBOX/USDT", "PYTH/USDT", "PYR/USDT", "ONE/USDT"]

# Force DB path
DB_PATH = os.path.join(os.path.dirname(__file__), "mini_aladdin_backtest.db")

# Check DB exists and tables
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()
print("DB Tables Found:", tables)
conn.close()

# Trading functions
def get_fingerprint_match(symbol, volume_spike, fakeouts, cons_days):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT gain_pct FROM fingerprints
        WHERE symbol = ?
    """, (symbol,))
    data = c.fetchall()
    conn.close()

    if not data:
        return 0, 0.0

    matches = len(data)
    # Example: naive win rate calc
    win_rate = min(95, 50 + matches / 2)
    return matches, win_rate

def generate_signal(symbol):
    # Placeholder: simulate signal logic
    volume_spike = random.random()
    fakeouts = random.randint(0, 2)
    cons_days = random.randint(1, 5)

    matches, win_rate = get_fingerprint_match(symbol, volume_spike, fakeouts, cons_days)

    if matches > 0 and win_rate >= 80:
        return f"🔥 BUY {symbol} | Matches={matches} | WinRate={win_rate:.1f}%"
    else:
        return None

# Main loop
while True:
    for coin in WATCHLIST:
        signal = generate_signal(coin)
        if signal:
            bot.send_message(chat_id=CHAT_ID, text=signal)
            print(signal)
        else:
            print(f"No signal for {coin}")

    # Hourly heartbeat
    bot.send_message(chat_id=CHAT_ID, text=f"🤖 Devil Bot Alive: {datetime.datetime.now()}")

    # Sleep 1 hour before next check
    time.sleep(3600)
