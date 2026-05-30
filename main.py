import os
import sys
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

PORT = int(os.getenv("PORT", 10000))
BT = os.getenv("BOT_TOKEN", "8654418214:AAEoExJis5sUNgLgNWjASFTe11sxTJp7Ld0")

bot = Bot(token=BT)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

@router.message(Command("start"))
async def start(msg: Message):
    print(f"✅ /start от {msg.from_user.full_name}")
    await msg.answer("Привет! Бот работает! 🚀")

@router.message()
async def echo(msg: Message):
    print(f"📩 {msg.from_user.full_name}: {msg.text}")
    await msg.answer(f"Эхо: {msg.text}")

async def index(request):
    return web.Response(text="OK")

async def main():
    dp.include_router(router)
    
    print("Удаляю вебхук...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("Запускаю поллинг...")
    # Запускаем поллинг
    polling_task = asyncio.create_task(dp.start_polling(bot))
    
    # Ждем 3 секунды
    await asyncio.sleep(3)
    
    # Проверяем бота
    try:
        me = await bot.get_me()
        print(f"✅ Бот @{me.username} готов!")
    except Exception as e:
        print(f"❌ Ошибка бота: {e}")
    
    # Запускаем веб-сервер
    app = web.Application()
    app.router.add_get("/", index)
    print(f"🌐 Сервер: порт {PORT}")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    
    print("✅ Все готово! Жду сообщения...")
    
    # Держим сервер
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main()) 
