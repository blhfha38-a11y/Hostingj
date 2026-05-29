import telebot, os
from flask import Flask, request

BOT_TOKEN = "8603622469:AAHHcTA6oV4gbcyBTqlRRU7TRY_irCZR5_Q"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✅ Бот работает!")

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode('utf-8'))])
    return 'ok', 200

@app.route('/')
def index():
    return 'Bot OK'

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://hostingj.onrender.com/webhook/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
