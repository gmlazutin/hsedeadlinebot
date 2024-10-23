import asyncio
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from db import init_db

bot = Bot(token=sys.argv[1])
dp = Dispatcher()

# Обработчик простого текстового сообщения
@dp.message()
async def text_message_handler(message: types.Message, state: FSMContext):
    await message.answer("msg dummy handler")

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
