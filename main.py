import os
import logging
import sys
import threading
from flask import Flask, request
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

# Flask для Render
app = Flask(__name__)

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

BT = os.getenv("BOT_TOKEN", "8654418214:AAEoExJis5sUNgLgNWjASFTe11sxTJp7Ld0")
AID = 6927128515

# На Render нужно использовать PORT из переменных окружения
PORT = int(os.getenv("PORT", 10000))

state_storage = StateMemoryStorage()
bot = TeleBot(BT, state_storage=state_storage)

class Os(StatesGroup):
    c = State()
    p = State()
    w = State()

cts = ["Москва", "Санкт-Петербург", "Екатеринбург", "Казань", "Новосибирск", "Краснодар"]
prd = {
    "Москва": {"@мфет@мин": "1г – 1500₽", "Мефедр0н": "1г – 2000₽", "Г@шиш": "1г – 1200₽", "К0к@ин": "0.5г – 6000₽"},
    "Санкт-Петербург": {"@мфетамин": "1г – 1400₽", "Мефедр0н": "1г – 1900₽", "Г@шиш": "1г – 1100₽", "МДМ@": "1г – 2500₽"},
    "Екатеринбург": {"@мфетамин": "1г – 1300₽", "Мефедр0н": "1г – 1800₽", "Г@шиш": "1г – 1000₽", "ЛСД": "1шт – 800₽"},
    "Казань": {"@мфет@мин": "1г – 1450₽", "Мефедр0н": "1г – 1950₽", "Г@шиш": "1г – 1150₽", "Экстази": "1шт – 1200₽"},
    "Новосибирск": {"@мфетамин": "1г – 1350₽", "Мефедр0н": "1г – 1850₽", "Г@шиш": "1г – 1050₽", "М@рки": "2шт – 1500₽"},
    "Краснодар": {"@мфетамин": "1г – 1550₽", "Мефедр0н": "1г – 2050₽", "Г@шиш": "1г – 1250₽", "Кок@ин": "0.5г – 6200₽"}
}
pdt = "\n".join(["💳 Карта: 4276 1234 5678 9012", "💰 Сумма по заказу", "📝 После оплаты отправьте скриншот"])
rvw = "Отзывы: @ghpityuogg"
sup = "bog_gmail"

def mm():
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton("🛒 ЗАКАЗАТЬ", callback_data="o"),
        InlineKeyboardButton("⭐ ОТЗЫВЫ", callback_data="r"),
        InlineKeyboardButton("🆘 ПОДДЕРЖКА", callback_data="s"),
        InlineKeyboardButton("📜 ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ", url="https://t.me/gggvppppq")
    )

def ck():
    kb = InlineKeyboardMarkup(row_width=1)
    for c in cts:
        kb.add(InlineKeyboardButton(c, callback_data=f"c_{c}"))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="m"))
    return kb

def pk(city):
    kb = InlineKeyboardMarkup(row_width=1)
    for prod, price in prd.get(city, {}).items():
        kb.add(InlineKeyboardButton(f"{prod} - {price}", callback_data=f"p_{city}_{prod}"))
    kb.add(InlineKeyboardButton("🔙 Выбрать город", callback_data="o"))
    kb.add(InlineKeyboardButton("🏠 Главное меню", callback_data="m"))
    return kb

def pm():
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton("📸 Отправить скриншот", callback_data="ss"),
        InlineKeyboardButton("❌ Отмена", callback_data="m")
    )

def cm():
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton("❌ Отмена", callback_data="m")
    )

@bot.message_handler(commands=['start'])
def st(msg: Message):
    bot.send_message(msg.chat.id,
        "🌟 NEBULA MARKET\n\nВыберите действие:",
        reply_markup=mm())

@bot.callback_query_handler(func=lambda call: call.data == "m")
def bm(cb: CallbackQuery):
    bot.delete_state(cb.from_user.id, cb.message.chat.id)
    bot.edit_message_text("🌟 NEBULA MARKET\n\nВыберите действие:", cb.message.chat.id, cb.message.message_id, reply_markup=mm())
    bot.answer_callback_query(cb.id)

@bot.callback_query_handler(func=lambda call: call.data == "r")
def sr(cb: CallbackQuery):
    bot.edit_message_text(f"⭐ Отзывы:\n{rvw}", cb.message.chat.id, cb.message.message_id, reply_markup=cm())
    bot.answer_callback_query(cb.id)

@bot.callback_query_handler(func=lambda call: call.data == "s")
def ss(cb: CallbackQuery):
    bot.edit_message_text(f"🆘 Поддержка: @{sup}", cb.message.chat.id, cb.message.message_id, reply_markup=cm())
    bot.answer_callback_query(cb.id)

@bot.callback_query_handler(func=lambda call: call.data == "o")
def osc(cb: CallbackQuery):
    bot.set_state(cb.from_user.id, Os.c, cb.message.chat.id)
    bot.edit_message_text("🏙 Выберите город:", cb.message.chat.id, cb.message.message_id, reply_markup=ck())
    bot.answer_callback_query(cb.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("c_"), state=Os.c)
def occ(cb: CallbackQuery):
    city = cb.data.split("_", 1)[1]
    bot.add_data(cb.from_user.id, cb.message.chat.id, ct=city)
    bot.set_state(cb.from_user.id, Os.p, cb.message.chat.id)
    bot.edit_message_text(f"🏙 Город: {city}\n\n📦 Товар:", cb.message.chat.id, cb.message.message_id, reply_markup=pk(city))
    bot.answer_callback_query(cb.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("p_"), state=Os.p)
def ocp(cb: CallbackQuery):
    parts = cb.data.split("_")
    city = parts[1]
    prod = "_".join(parts[2:])
    
    with bot.retrieve_data(cb.from_user.id, cb.message.chat.id) as data:
        data["ct"] = city
        data["pr"] = prod
        data["pc"] = prd[city][prod]
    
    with bot.retrieve_data(cb.from_user.id, cb.message.chat.id) as data:
        txt = f"✅ Заказ:\n🏙 {city}\n📦 {prod}\n💰 {data['pc']}\n\n💳 Оплата:\n{pdt}"
    
    bot.set_state(cb.from_user.id, Os.w, cb.message.chat.id)
    bot.edit_message_text(txt, cb.message.chat.id, cb.message.message_id, reply_markup=pm())
    bot.answer_callback_query(cb.id)

@bot.callback_query_handler(func=lambda call: call.data == "ss", state=Os.w)
def rqs(cb: CallbackQuery):
    bot.edit_message_text("📸 Отправьте скриншот перевода (только фото).\nДля отмены нажмите кнопку.", cb.message.chat.id, cb.message.message_id, reply_markup=cm())
    bot.answer_callback_query(cb.id)

@bot.message_handler(content_types=['photo'], state=Os.w)
def hps(msg: Message):
    with bot.retrieve_data(msg.from_user.id, msg.chat.id) as data:
        city = data.get("ct", "-")
        prod = data.get("pr", "-")
        price = data.get("pc", "-")
    
    cap = (f"📸 Новый скриншот\nОт: @{msg.from_user.username or 'no name'} ({msg.from_user.id})\n"
           f"{msg.from_user.full_name}\nГород: {city}\nТовар: {prod}\nЦена: {price}")
    try:
        bot.send_photo(AID, msg.photo[-1].file_id, caption=cap)
        bot.send_message(msg.chat.id, "✅ Скриншот отправлен.", reply_markup=mm())
    except:
        bot.send_message(msg.chat.id, "⚠️ Ошибка. Свяжитесь с @" + sup, reply_markup=mm())
    
    bot.delete_state(msg.from_user.id, msg.chat.id)

@bot.message_handler(state=Os.w)
def wps(msg: Message):
    bot.send_message(msg.chat.id, "Пожалуйста, отправьте фото.", reply_markup=cm())

# Webhook для Render
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return '!'

# Health check для Render
@app.route('/')
def index():
    return 'Bot is running!'

if __name__ == "__main__":
    print("=" * 40)
    print("ЗАПУСК БОТА")
    print("=" * 40)
    
    try:
        me = bot.get_me()
        print(f"✅ Бот подключен!")
        print(f"   Имя: {me.first_name}")
        print(f"   Юзернейм: @{me.username}")
        print(f"   ID: {me.id}")
        print(f"   Ссылка: https://t.me/{me.username}")
        print("=" * 40)
        
        # Удаляем старый вебхук и запускаем поллинг в отдельном потоке
        bot.remove_webhook()
        
        # Запускаем поллинг в фоне
        threading.Thread(target=bot.infinity_polling, daemon=True).start()
        
        # Запускаем Flask
        print(f"Сервер запущен на порту {PORT}")
        app.run(host='0.0.0.0', port=PORT)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
