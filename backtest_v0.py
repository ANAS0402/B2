import os
import sqlite3
import ccxt
import pandas as pd
from datetime import datetime, timedelta

# Force DB to stay in project folder
DB_PATH = os.path.join(os.path.dirname(__file__), "mini_aladdin_backtest.db")

WATCHLIST = ["CFX/USDT", "BLUR/USDT", "JUP/USDT", "MBOX/USDT", "PYTH/USDT", "PYR/USDT", "ONE/USDT"]

# Connect to SQLite DB
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Create table if not exists
c.execute("""
CREATE TABLE IF NOT EXISTS fingerprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    timestamp TEXT,
    gain_pct REAL
)
""")
conn.commit()

print("Building fingerprint DB...")

exchange = ccxt.binance()
for symbol in WATCHLIST:
    print(f"Building fingerprint for {symbol}...")

    try:
        # Fetch last 500 candles (1d timeframe)
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1d', limit=500)
        df = pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
        df['gain_pct'] = df['close'].pct_change() * 100

        # Identify "fingerprints" of 100%+ runs
        for i in range(1, len(df)):
            if df['close'][i] > df['close'][i-1] * 2:  # 100% gain
                c.execute("INSERT INTO fingerprints (symbol, timestamp, gain_pct) VALUES (?, ?, ?)",
                          (symbol, datetime.utcfromtimestamp(df['ts'][i]/1000).isoformat(), df['gain_pct'][i]))
        conn.commit()
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")

print("Fingerprint DB created ✅")
conn.close()
