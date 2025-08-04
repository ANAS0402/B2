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

DB_PATH = os.path.join(os.path.dirname(__file__), "mini_aladdin_backtest.db")

# ✅ 1. Ensure DB and table exist
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS fingerprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    timestamp TEXT,
    gain_pct REAL
)
""")
conn.commit()

# Check tables
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()
print("DB Tables Found:", tables)

# ✅ 2. If fingerprints empty, auto-build minimal fingerprints
c.execute("SELECT COUNT(*) FROM fingerprints;")
count = c.fetchone()[0]

if count == 0:
    print("No fingerprints found. Building minimal DB...")
    exchange = ccxt.binance()
    for symbol in WATCHLIST:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1d', limit=30)
            for candle in ohlcv:
                ts, o, h, l, cl, vol = candle
                gain_pct = ((cl - o) / o) * 100
                if gain_pct >= 100:  # 100% day
                    c.execute("INSERT INTO fingerprints (symbol, timestamp, gain_pct) VALUES (?, ?, ?)",
                              (symbol, datetime.datetime.utcfromtimestamp(ts/1000).isoformat(), gain_pct))
            conn.commit()
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

conn.close()
