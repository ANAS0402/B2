import sqlite3
import datetime
import ccxt
import threading
import time
from telegram import Bot
from flask import Flask

DB_PATH = "mini_aladdin_backtest.db"
TELEGRAM_TOKEN = "8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo"
CHAT_ID = "1873122742"

bot = Bot(token=TELEGRAM_TOKEN)

# ---- Bot Logic ----
def run_bot():
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = c.fetchall()
            print("DB Tables Found:", tables)
            conn.close()
            
            bot.send_message(chat_id=CHAT_ID, text=f"🤖 Devil Bot Alive {datetime.datetime.now()}")
        except Exception as e:
            print("Error in bot loop:", e)
        time.sleep(60)  # every minute

# ---- Flask Dummy Server ----
app = Flask(__name__)

@app.route('/')
def home():
    return "Devil Bot is Running!"

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=10000)  # Render detects this port
