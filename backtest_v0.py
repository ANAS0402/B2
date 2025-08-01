"""
Mini Aladdin - Backtest Engine v0.1
Builds 10y fingerprint DB of 2× pumps
"""

import ccxt, pandas as pd, numpy as np, sqlite3, time, datetime

WATCHLIST = ["CFX/USDT", "BLUR/USDT", "JUP/USDT", "MBOX/USDT", "PYTH/USDT", "PYR/USDT", "ONE/USDT"]
DB_PATH = "mini_aladdin_backtest.db"

exchange = ccxt.binance()

# ==============================
# DB Setup
# ==============================
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS fingerprints(
    symbol TEXT,
    timestamp INT,
    volume_spike REAL,
    fakeout_count INT,
    pre_consolidation_days INT,
    gain_pct REAL
)
""")
conn.commit()

def fetch_ohlcv(symbol):
    try:
        data = exchange.fetch_ohlcv(symbol, timeframe='1d', limit=1000)
        df = pd.DataFrame(data, columns=['time','open','high','low','close','volume'])
        return df
    except:
        return None

for coin in WATCHLIST:
    df = fetch_ohlcv(coin)
    if df is None: 
        continue
    print(f"Building fingerprint for {coin}...")

    for i in range(10, len(df)-1):
        window = df.iloc[i-7:i]
        current = df.iloc[i]
        future = df.iloc[i+1:i+8]  # look ahead 1 week

        vol_spike = current['volume'] / (window['volume'].mean()+1e-9)
        fakeouts = (window['low'] < window['close'].iloc[-1]*0.97).sum()
        cons_days = round(1/(window['close'].std()/window['close'].mean()+0.0001))
        gain_pct = ((future['high'].max() - current['close']) / current['close'])*100

        if gain_pct >= 50:  # record only meaningful moves
            c.execute("INSERT INTO fingerprints VALUES (?,?,?,?,?,?)",
                      (coin, int(current['time']), vol_spike, fakeouts, cons_days, gain_pct))

conn.commit()
conn.close()
print("Fingerprint DB created ✅")
