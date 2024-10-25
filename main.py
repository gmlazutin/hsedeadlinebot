import asyncio
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
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

# Отправка пользователю напоминания
async def send_reminder(id: int, user_id: int, task_text: str, deadline: str, category: str, priority: int, alerts_sent: int):
    pl = ""
    if alerts_sent == 0:
        pl = "менее 24 часов"
    elif alerts_sent == 1:
        pl = "менее 12 часов"
    elif alerts_sent == 2:
        pl = "менее 6 часов"
    elif alerts_sent == 3:
        pl = "менее 2 часов"
    elif alerts_sent == 4:
        pl = "менее 30 минут"
    
    text = f"\nДедлайн: {deadline}\nПриоритет: {priority_gen(priority)} ({priority})\nКатегория: {category}"

    if alerts_sent < 5:
        text = f"До завершения дедлайна по задаче \"{task_text}\" (ID: {id}) осталось: {pl}!\n\n"+text
    else:
        text = f"Задача \"{task_text}\" (ID: {id}) истекла!!!\n\n"+text
    
    await bot.send_message(user_id, text)


# Напоминание о задачах
async def reminder():
    while True:
        now = datetime.now()
        async with db_session() as db:
            async with db.execute('SELECT id, user_id, task_text, deadline, category, priority, alerts_sent FROM tasks WHERE next_alert_at <= ?', (now,)) as cursor:
                tasks = await cursor.fetchall()
                for task in tasks:
                    id, user_id, task_text, deadline, category, priority, alerts_sent = task
                    await send_reminder(id, user_id, task_text, deadline, category, priority, alerts_sent)
                    # Создаём транзакцию для инкремента кол-ва посланных алертов
                    # Далее идёт неочевидный SQL-запрос, если непонятно как он работает - пишите мне.
                    await db.execute('BEGIN TRANSACTION')

                    await db.execute('''UPDATE tasks 
                                            SET next_alert_at = DATETIME (deadline,
                                                CASE
                                                    WHEN alerts_sent+1 = 1 THEN '-12 hours'
                                                    WHEN alerts_sent+1 = 2 THEN '-6 hours'
                                                    WHEN alerts_sent+1 = 3 THEN '-2 hours'
                                                    WHEN alerts_sent+1 = 4 THEN '-30 minutes'
                                                    WHEN alerts_sent+1 = 5 THEN '+0 seconds'
                                                END)
                                            WHERE alerts_sent < 6 AND id = ?''', (id,))
                                        
                    await db.execute('''UPDATE tasks
                                            SET alerts_sent = alerts_sent + 1
                                            WHERE alerts_sent < 6 AND id = ?''', (id,))

                    await db.execute('DELETE FROM tasks WHERE alerts_sent = 6 AND id = ?', (id,))
                                     
                    await db.execute('COMMIT')
        await asyncio.sleep(60)  # Проверка каждую минуту

async def main():
    await init_db()
    asyncio.create_task(reminder())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
