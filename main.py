"""
Mini Aladdin - Devil Mode v1.0
Aggressive, Memory-Integrated, Fail-Deletion Enabled
"""

import ccxt, pandas as pd, numpy as np, sqlite3, time, datetime, logging
from telegram import Bot

# ===============================
# CONFIG
# ===============================
WATCHLIST = ["CFX/USDT", "BLUR/USDT", "JUP/USDT", "MBOX/USDT", "PYTH/USDT", "PYR/USDT", "ONE/USDT"]
DB_PATH = "mini_aladdin_backtest.db"
TELEGRAM_TOKEN = "8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo"
CHAT_ID = "1873122742"

bot = Bot(token=TELEGRAM_TOKEN)
exchange = ccxt.binance()
logging.basicConfig(filename='devil_log.txt', level=logging.INFO)

# Fail-deletion memory
FAIL_PATTERNS = {}

# ===============================
# DB Connection
# ===============================
def get_fingerprint_match(symbol, vol_spike, fakeouts, cons_days):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    vol_low, vol_high = vol_spike*0.7, vol_spike*1.3
    fake_low, fake_high = max(0,fakeouts-1), fakeouts+1
    cons_low, cons_high = max(1,cons_days-2), cons_days+2
    
    c.execute("""SELECT gain_pct FROM fingerprints
                 WHERE symbol=? 
                 AND volume_spike BETWEEN ? AND ?
                 AND fakeout_count BETWEEN ? AND ?
                 AND pre_consolidation_days BETWEEN ? AND ?""",
                 (symbol, vol_low, vol_high, fake_low, fake_high, cons_low, cons_high))
    rows = c.fetchall()
    conn.close()
    
    if len(rows)==0:
        return 0, 0
    win_events = [r[0] for r in rows if r[0] >= 100]
    win_rate = len(win_events)/len(rows)*100
    return len(rows), win_rate

# ===============================
# IQ Scoring (placeholder logic)
# ===============================
def compute_iq(df):
    # Simple placeholder for Whale + Volume + Social score
    vol_ratio = df['volume'].iloc[-1] / df['volume'].iloc[-20:].mean()
    price_slope = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5] * 100
    whale_score = min(40, vol_ratio*5)
    social_score = np.random.randint(0,20)
    return min(100, whale_score+social_score+max(0,price_slope))

# ===============================
# Signal Generator
# ===============================
def generate_signal(symbol):
    df = fetch_ohlcv(symbol)
    if df is None or len(df)<30:
        return None

    # Compute fingerprint features
    volume_spike = df['volume'].iloc[-1] / df['volume'].iloc[-7:].mean()
    fakeouts = (df['low'].iloc[-5:] < df['close'].iloc[-6]).sum()
    cons_days = round(1/(df['close'].iloc[-7:].std()/df['close'].iloc[-7:].mean()+0.0001))
    iq_score = compute_iq(df)

    # Fail deletion check
    fp_key = (round(volume_spike,1), fakeouts, cons_days)
    if fp_key in FAIL_PATTERNS and FAIL_PATTERNS[fp_key] >= 2:
        return None  # Auto-ignore repeated bad pattern

    # Fingerprint historical match
    matches, win_rate = get_fingerprint_match(symbol, volume_spike, fakeouts, cons_days)
    if iq_score < 70 or win_rate < 60:
        return None

    # Compute entry / stop / target
    entry = df['close'].iloc[-1]
    stop = round(entry*0.9, 4)
    target = round(entry*2, 4)
    
    return {
        "symbol": symbol,
        "entry": entry,
        "target": target,
        "stop": stop,
        "confidence": iq_score,
        "win_rate": win_rate,
        "pattern_key": fp_key
    }

# ===============================
# Data Fetch
# ===============================
def fetch_ohlcv(symbol):
    try:
        data = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100)
        df = pd.DataFrame(data, columns=['time','open','high','low','close','volume'])
        return df
    except:
        return None

# ===============================
# Main Loop
# ===============================
while True:
    for coin in WATCHLIST:
        signal = generate_signal(coin)
        if signal:
            msg = f"""
⚡ Mini Aladdin DEVIL 2× Signal

Coin: {signal['symbol']}
Entry: {signal['entry']}
Target: {signal['target']}
Stop: {signal['stop']}
Confidence: {signal['confidence']}%
Historical Win Rate: {signal['win_rate']}%
Fail-Deletion Active ✅
"""
            bot.send_message(chat_id=CHAT_ID, text=msg)
            logging.info(f"{datetime.datetime.now()} | {signal}")

            # Simulate post-trade monitoring (paper)
            # If fail quickly, add to fail patterns
            if signal['confidence']<75:
                FAIL_PATTERNS[signal['pattern_key']] = FAIL_PATTERNS.get(signal['pattern_key'],0)+1

    time.sleep(3600)  # Run hourly for now
