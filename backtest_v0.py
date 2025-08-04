import ccxt, pandas as pd, sqlite3, os

WATCHLIST = ["CFX/USDT", "BLUR/USDT", "JUP/USDT", "MBOX/USDT", "PYTH/USDT", "PYR/USDT", "ONE/USDT"]
DB_PATH = "mini_aladdin_backtest.db"

print("Building fingerprint DB...")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS fingerprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    volume_spike REAL,
    fakeout_count INTEGER,
    pre_consolidation_days INTEGER,
    gain_pct REAL
)''')

exchange = ccxt.binance()

for symbol in WATCHLIST:
    print(f"Building fingerprint for {symbol}...")
    try:
        data = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=500)
        df = pd.DataFrame(data, columns=['time','open','high','low','close','volume'])
        if len(df) < 50:
            continue
        for i in range(20, len(df)-5):
            vol_spike = df['volume'].iloc[i] / df['volume'].iloc[i-7:i].mean()
            fakeouts = (df['low'].iloc[i-5:i] < df['close'].iloc[i-6]).sum()
            cons_days = round(1/(df['close'].iloc[i-7:i].std()/df['close'].iloc[i-7:i].mean()+0.0001))
            future_gain = df['high'].iloc[i+5:i+20].max()/df['close'].iloc[i]*100-100
            c.execute("INSERT INTO fingerprints(symbol, volume_spike, fakeout_count, pre_consolidation_days, gain_pct) VALUES (?,?,?,?,?)",
                      (symbol, vol_spike, fakeouts, cons_days, future_gain))
        conn.commit()
    except Exception as e:
        print(f"Error {symbol}: {e}")

conn.close()
print("Fingerprint DB created ✅")
