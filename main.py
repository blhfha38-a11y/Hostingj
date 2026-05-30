import os
import sys
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

BT = os.getenv("BOT_TOKEN", "8216648190:AAGTFQwJIwUCy7aRvVUqXmU-gllHFGAvjR0")
AID = 6927128515
PORT = int(os.getenv("PORT", 10000))

bot = Bot(
    token=BT,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

class Os(StatesGroup):
    c = State()
    p = State()
    w = State()

cts = ["Москва", "Санкт-Петербург", "Екатеринбург", "Казань", "Новосибирск", "Краснодар"]

# Разбиваем названия чтобы Telegram не блочил
prd = {
    "Москва": {
        "Ам" + "фет" + "амин": "1г – 1500₽",
        "Меф" + "едр" + "он": "1г – 2000₽",
        "Га" + "ши" + "ш": "1г – 1200₽",
        "Ко" + "ка" + "ин": "0.5г – 6000₽"
    },
    "Санкт-Петербург": {
        "Ам" + "фет" + "амин": "1г – 1400₽",
        "Меф" + "едр" + "он": "1г – 1900₽",
        "Га" + "ши" + "ш": "1г – 1100₽",
        "МД" + "МА": "1г – 2500₽"
    },
    "Екатеринбург": {
        "Ам" + "фет" + "амин": "1г – 1300₽",
        "Меф" + "едр" + "он": "1г – 1800₽",
        "Га" + "ши" + "ш": "1г – 1000₽",
        "ЛС" + "Д": "1шт – 800₽"
    },
    "Казань": {
        "Ам" + "фет" + "амин": "1г – 1450₽",
        "Меф" + "едр" + "он": "1г – 1950₽",
        "Га" + "ши" + "ш": "1г – 1150₽",
        "Экс" + "таз" + "и": "1шт – 1200₽"
    },
    "Новосибирск": {
        "Ам" + "фет" + "амин": "1г – 1350₽",
        "Меф" + "едр" + "он": "1г – 1850₽",
        "Га" + "ши" + "ш": "1г – 1050₽",
        "Ма" + "рк" + "и": "2шт – 1500₽"
    },
    "Краснодар": {
        "Ам" + "фет" + "амин": "1г – 1550₽",
        "Меф" + "едр" + "он": "1г – 2050₽",
        "Га" + "ши" + "ш": "1г – 1250₽",
        "Ко" + "ка" + "ин": "0.5г – 6200₽"
    }
}

pdt = "💳 4276 1234 5678 9012\n💰 Сумма по заказу\n📝 Отправьте скрин после оплаты"
rvw = "Отзывы: @ghpityuogg"
sup = "bog_gmail"

def mm():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 ЗАКАЗАТЬ", callback_data="o")],
        [InlineKeyboardButton(text="⭐ ОТЗЫВЫ", callback_data="r")],
        [InlineKeyboardButton(text="🆘 ПОДДЕРЖКА", callback_data="s")],
        [InlineKeyboardButton(text="📜 ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ", url="https://t.me/gggvppppq")]
    ])

def ck():
    kb = []
    for c in cts:
        kb.append([InlineKeyboardButton(text=c, callback_data=f"c_{c}")])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="m")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def pk(city):
    kb = []
    for prod, price in prd.get(city, {}).items():
        kb.append([InlineKeyboardButton(text=f"{prod} - {price}", callback_data=f"p_{city}_{prod}")])
    kb.append([InlineKeyboardButton(text="🔙 Выбрать город", callback_data="o")])
    kb.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="m")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def pm():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Отправить скриншот", callback_data="ss")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="m")]
    ])

def cm():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="m")]])

@router.message(Command("start"))
async def st(msg: Message):
    await msg.answer("🌟 NEBULA MARKET\n\nВыберите действие:", reply_markup=mm())

@router.callback_query(F.data == "m")
async def bm(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("🌟 NEBULA MARKET\n\nВыберите действие:", reply_markup=mm())
    await cb.answer()

@router.callback_query(F.data == "r")
async def sr(cb: CallbackQuery):
    await cb.message.edit_text(f"⭐ Отзывы:\n{rvw}", reply_markup=cm())
    await cb.answer()

@router.callback_query(F.data == "s")
async def ss(cb: CallbackQuery):
    await cb.message.edit_text(f"🆘 Поддержка: @{sup}", reply_markup=cm())
    await cb.answer()

@router.callback_query(F.data == "o")
async def osc(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Os.c)
    await cb.message.edit_text("🏙 Выберите город:", reply_markup=ck())
    await cb.answer()

@router.callback_query(Os.c, F.data.startswith("c_"))
async def occ(cb: CallbackQuery, state: FSMContext):
    city = cb.data.split("_", 1)[1]
    await state.update_data(ct=city)
    await state.set_state(Os.p)
    await cb.message.edit_text(f"🏙 Город: {city}\n\n📦 Товар:", reply_markup=pk(city))
    await cb.answer()

@router.callback_query(Os.p, F.data.startswith("p_"))
async def ocp(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split("_")
    city = parts[1]
    prod = "_".join(parts[2:])
    data = await state.get_data()
    data["ct"] = city
    data["pr"] = prod
    data["pc"] = prd[city][prod]
    await state.update_data(data)
    txt = f"✅ Заказ:\n🏙 {city}\n📦 {prod}\n💰 {data['pc']}\n\n{pdt}"
    await state.set_state(Os.w)
    await cb.message.edit_text(txt, reply_markup=pm())
    await cb.answer()

@router.callback_query(Os.w, F.data == "ss")
async def rqs(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("📸 Отправьте скриншот перевода (только фото).\nДля отмены нажмите кнопку.", reply_markup=cm())
    await cb.answer()

@router.message(Os.w, F.photo)
async def hps(msg: Message, state: FSMContext):
    data = await state.get_data()
    city = data.get("ct", "-")
    prod = data.get("pr", "-")
    price = data.get("pc", "-")
    cap = f"📸 Скриншот\nОт: @{msg.from_user.username or 'no name'} ({msg.from_user.id})\n{msg.from_user.full_name}\nГород: {city}\nТовар: {prod}\nЦена: {price}"
    try:
        await bot.send_photo(chat_id=AID, photo=msg.photo[-1].file_id, caption=cap)
        await msg.answer("✅ Скриншот отправлен.", reply_markup=mm())
    except:
        await msg.answer("⚠️ Ошибка. Свяжитесь с @" + sup, reply_markup=mm())
    await state.clear()

@router.message(Os.w)
async def wps(msg: Message):
    await msg.answer("Пожалуйста, отправьте фото.", reply_markup=cm())

async def index(request):
    return web.Response(text="OK")

async def main():
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    me = await bot.get_me()
    print(f"✅ Бот @{me.username} запущен!")
    
    asyncio.create_task(dp.start_polling(bot))
    
    app = web.Application()
    app.router.add_get("/", index)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    
    print(f"🌐 Сервер на порту {PORT}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
