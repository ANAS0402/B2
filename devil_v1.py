import time

def run_bot():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    while True:
        for symbol in WATCHLIST:
            try:
                matches = c.execute("SELECT COUNT(*) FROM fingerprints WHERE symbol=?",(symbol,)).fetchone()[0]
                if matches > 0:
                    bot.send_message(chat_id=CHAT_ID,
                        text=f"✅ Fingerprints ready for {symbol} | {matches} patterns found.")
                else:
                    bot.send_message(chat_id=CHAT_ID,
                        text=f"⚠️ No patterns for {symbol} yet, still learning...")

            except Exception as e:
                bot.send_message(chat_id=CHAT_ID,
                    text=f"❌ Error for {symbol}: {str(e)}")

        time.sleep(3600)  # check every 1 hour

run_bot()
