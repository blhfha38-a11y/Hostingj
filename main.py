import os
import sys
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

PORT = int(os.getenv("PORT", 10000))
BT = os.getenv("BOT_TOKEN", "8654418214:AAEoExJis5sUNgLgNWjASFTe11sxTJp7Ld0")

bot = Bot(token=BT)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

@router.message(Command("start"))
async def start(msg: Message):
    print(f"✅ /start от @{msg.from_user.username} ({msg.from_user.id})")
    await msg.answer("Привет! Бот работает! 🚀")

@router.message()
async def echo(msg: Message):
    await msg.answer(f"Ты написал: {msg.text}")

async def index(request):
    return web.Response(text="OK")

async def run_bot():
    print("🤖 Бот запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

async def main():
    dp.include_router(router)
    asyncio.create_task(run_bot())
    app = web.Application()
    app.router.add_get("/", index)
    print(f"🌐 Сервер на порту {PORT}")
    await web._run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    asyncio.run(main()) 
