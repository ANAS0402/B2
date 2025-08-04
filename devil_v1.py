import os
import time
import datetime
import sqlite3
from telegram import Bot

# ---------------- CONFIG ----------------
TELEGRAM_TOKEN = "8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo"
CHAT_ID = "1873122742"
DB_PATH = "mini_aladdin_backtest.db"
WATCHLIST = ["CFX", "BLUR", "JUP", "MBOX", "PYTH", "PYR", "ONE"]

bot = Bot(token=TELEGRAM_TOKEN)

# ---------------- FUNCTIONS ----------------

def check_fingerprints(symbol):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS fingerprints(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            gain_pct REAL
        )
    """)
    conn.commit()

    # Count how many patterns for this symbol
    c.execute("SELECT COUNT(*) FROM fingerprints WHERE symbol=?", (symbol,))
    matches = c.fetchone()[0]
    conn.close()
    return matches

def run_bot():
    bot.send_message(chat_id=CHAT_ID, text="🤖 Devil Bot Started...")

    while True:
        for symbol in WATCHLIST:
            try:
                matches = check_fingerprints(symbol)
                if matches > 0:
                    bot.send_message(chat_id=CHAT_ID,
                        text=f"✅ {symbol}: {matches} patterns found in DB.")
                else:
                    bot.send_message(chat_id=CHAT_ID,
                        text=f"⚠️ {symbol}: No patterns yet, still learning.")

            except Exception as e:
                bot.send_message(chat_id=CHAT_ID,
                    text=f"❌ Error for {symbol}: {str(e)}")

        time.sleep(3600)  # check every 1 hour

# ---------------- START ----------------
if __name__ == "__main__":
    run_bot()
