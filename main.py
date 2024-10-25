import asyncio
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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

# Состояния создания задач для машины состояний
class AddTaskStates(StatesGroup):
    waiting_for_task_text = State()
    waiting_for_deadline = State()
    waiting_for_category = State()
    waiting_for_priority = State()

# Обработчик команды /add для начала добавления задачи
@dp.message(Command("add"))
async def add_task_start(message: types.Message, state: FSMContext):
    await message.answer("Введите текст задачи.")
    await state.set_state(AddTaskStates.waiting_for_task_text)

# Получаем описание задачи
@dp.message(AddTaskStates.waiting_for_task_text)
async def process_task_text(message: types.Message, state: FSMContext):
    await state.update_data(task_text=message.text)
    await message.answer("Введите дедлайн задачи в формате YYYY-MM-DD HH:MM.")
    await state.set_state(AddTaskStates.waiting_for_deadline)

# Получаем дедлайн задачи
@dp.message(AddTaskStates.waiting_for_deadline)
async def process_deadline(message: types.Message, state: FSMContext):
    try:
        deadline = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("Неверный формат даты. Введите в формате YYYY-MM-DD HH:MM.")
        return
    await state.update_data(deadline=deadline)
    await message.answer("Введите категорию задачи.")
    await state.set_state(AddTaskStates.waiting_for_category)

# Получаем категорию задачи
@dp.message(AddTaskStates.waiting_for_category)
async def process_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Введите приоритет задачи (1-3).")
    await state.set_state(AddTaskStates.waiting_for_priority)

# Получаем приоритет задачи
@dp.message(AddTaskStates.waiting_for_priority)
async def process_priority(message: types.Message, state: FSMContext):
    try:
        priority = int(message.text)
        if priority not in (1, 2, 3):
            raise ValueError
    except ValueError:
        await message.answer("Приоритет должен быть числом от 1 до 3.")
        return

    await state.update_data(priority=priority)
    data = await state.get_data()

    # Определяем начальное значение alerts_sent
    now = datetime.now()
    time_diff = data['deadline'] - now
    if time_diff > timedelta(hours=24):
        alerts_sent = 0
    elif time_diff > timedelta(hours=12):
        alerts_sent = 1
    elif time_diff > timedelta(hours=6):
        alerts_sent = 2
    elif time_diff > timedelta(hours=2):
        alerts_sent = 3
    elif time_diff > timedelta(minutes=30):
        alerts_sent = 4
    else:
        alerts_sent = 5

    # Вставка данных в базу
    async with db_session() as db:
        await db.execute('''INSERT INTO tasks (user_id, task_text, deadline, category, priority, alerts_sent, next_alert_at) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                            (message.from_user.id, data['task_text'], data['deadline'], data['category'], data['priority'], alerts_sent, data['deadline']))
        await db.commit()

    await message.answer("Задача добавлена!")
    await state.clear()

# Состояния завершения задачи для машины состояний
class CompleteTaskStates(StatesGroup):
    waiting_for_task_id = State()

@dp.message(Command("complete"))
async def complete_task_start(message: types.Message, state: FSMContext):
    # Получаем задачи из базы данных
    async with db_session() as db:
        async with db.execute('SELECT id, task_text, deadline FROM tasks WHERE user_id = ? ORDER BY deadline', (message.from_user.id,)) as cursor:
            tasks = await cursor.fetchall()

    # Проверяем, есть ли у пользователя задачи
    if tasks:
        response = "Выберите задачу для завершения, отправив её ID:\n"
        for task in tasks:
            response += f"- {task[1]} (ID: {task[0]}) | Дедлайн: {task[2]}\n"
        await message.answer(response)
        await state.set_state(CompleteTaskStates.waiting_for_task_id)
    else:
        await message.answer("У вас нет задач для завершения.")

@dp.message(CompleteTaskStates.waiting_for_task_id)
async def process_task_id(message: types.Message, state: FSMContext):
    try:
        task_id = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный ID задачи.")
        return

    async with db_session() as db:
        # Получаем информацию о задаче перед ее удалением
        async with db.execute('SELECT task_text FROM tasks WHERE id = ? AND user_id = ?', (task_id, message.from_user.id)) as cursor:
            task = await cursor.fetchone()

        if task is None:
            await message.answer("Задача с таким ID не найдена. Проверьте ID и попробуйте снова.")
            return

        # Перенос задачи в таблицу выполненных
        await db.execute('INSERT INTO completed_tasks (user_id, task_text, completed_at) VALUES (?, ?, ?)',
                         (message.from_user.id, task[0], datetime.now()))
        await db.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, message.from_user.id))
        await db.commit()

    await message.answer(f"Задача с ID {task_id} успешно завершена.")
    await state.clear()

@dp.message(Command("statistic"))
async def view_statistics(message: types.Message):
    async with db_session() as db:
        async with db.execute("SELECT task_text, completed_at FROM completed_tasks WHERE user_id = ?", (message.from_user.id,)) as cursor:
            completed_tasks = await cursor.fetchall()

    if completed_tasks:
        response = "Завершенные задачи:\n\n"
        for task_text, completed_at in completed_tasks:
            response += f"- {task_text} (Завершено: {completed_at})\n"
    else:
        response = "У вас пока нет завершенных задач."

    await message.answer(response)


# Обработчик простого текстового сообщения
@dp.message()
async def text_message_handler(message: types.Message, state: FSMContext):
    await message.answer("Неизвестная команда. Введите /help для получения списка команд.")

async def main():
    await init_db()
    asyncio.create_task(reminder())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())