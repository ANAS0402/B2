# main.py

from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from telegram.ext import Updater, CommandHandler

# === Telegram Bot ===
TOKEN = '8223601715:AAE0iVYff1eS1M4jcFytEbd1jcFzV-b6fFo'  # 🔁 Replace this with your actual token

def start(update, context):
    update.message.reply_text("✅ Bot is alive and working on Render!")

def main_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()
    updater.idle()

# === Fake HTTP Server (for Render port binding) ===
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is alive!')

def run_server():
    server = HTTPServer(('0.0.0.0', 10000), KeepAliveHandler)
    server.serve_forever()

# === Start both server and bot ===
if __name__ == '__main__':
    threading.Thread(target=run_server).start()
    main_bot()
