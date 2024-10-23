import asyncio
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from db import init_db, db_session
from messages import priority_gen

bot = Bot(token=sys.argv[1])
dp = Dispatcher()

# Просмотр задач по категориям
@dp.message(Command("tasks"))
async def view_tasks(message: types.Message):
    async with db_session() as db:
        async with db.execute('SELECT id, task_text, deadline, category, priority FROM tasks WHERE user_id = ? ORDER BY deadline', (message.from_user.id,)) as cursor:
            tasks = await cursor.fetchall()

    if tasks:
        cat = {}
        for task in tasks:
            category = str(task[3])
            if category not in cat:
                cat[category] = []
            cat[category].append([task[0], task[1], task[2], task[4]])
        response = ""
        for c in cat:
            response += f"Категория \"{c}\":\n"
            for t in cat[c]:
                #todo (issue #2): нормальное форматирование даты
                response += f"- Задача: {t[1]} (ID: {t[0]})\n  Дедлайн: {t[2]}\n  Приоритет: {priority_gen(t[3])} ({t[3]})\n"
            response += "\n"
        await message.answer(response)
    else:
        await message.answer("У вас нет задач.")

# Обработчик простого текстового сообщения
@dp.message()
async def text_message_handler(message: types.Message, state: FSMContext):
    await message.answer("Неизвестная команда. Введите /help для получения списка команд.")

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
