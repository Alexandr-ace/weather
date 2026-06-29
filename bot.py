import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Импортируем роутер из handlers.py
from main import router

load_dotenv()

# 🔑 ВОТ ТУТ НУЖЕН BOT_TOKEN!
BOT_TOKEN = os.environ["BOT_TOKEN"]
if not BOT_TOKEN:
    raise ValueError("ОШИБКА: Переменная BOT_TOKEN не найдена!")

async def main():
    # 🔑 Создаем бота с токеном
    bot = Bot(token=BOT_TOKEN)
    
    # Создаем диспетчер (он управляет всеми сообщениями)
    dp = Dispatcher(storage=MemoryStorage())
    
    # 🔑 Подключаем ваш роутер с командами
    dp.include_router(router)
    
    # Запускаем бота
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())