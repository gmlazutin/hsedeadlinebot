import asyncio
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from aiogram.fsm.state import StatesGroup, State

from db import init_db, db_session
from messages import l10n

bot = Bot(token=sys.argv[1])
dp = Dispatcher()

def lang_ru():
    return l10n("ru")

#Генерирует текстовое описание приоритета исходя из его численного значения
def priority_gen(lang: dict[str, str], pri: int) -> str:
    if pri == 1:
        return lang["prilow"]
    if pri == 2:
        return lang["primedium"]
    if pri == 3:
        return lang["prihigh"]
    return lang["unknown"]

# Команда /help
@dp.message(Command("help"))
async def help_command(message: types.Message):
    msgs = lang_ru()
    await message.answer(msgs["helptext"])

# Просмотр задач по категориям
@dp.message(Command("tasks"))
async def view_tasks(message: types.Message):
    async with db_session() as db:
        async with db.execute('SELECT id, task_text, deadline, category, priority FROM tasks WHERE user_id = ? ORDER BY deadline', (message.from_user.id,)) as cursor:
            tasks = await cursor.fetchall()
    msgs = lang_ru()
    if tasks:
        cat = {}
        for task in tasks:
            category = str(task[3])
            if category not in cat:
                cat[category] = []
            cat[category].append([task[0], task[1], task[2], task[4]])
        response = ""
        for c in cat:
            response += msgs["viewtaskscat"] % (c) + "\n"
            for t in cat[c]:
                #todo (issue #2): нормальное форматирование даты
                response += msgs["viewtaskstask"] % (t[1], t[0], t[2], priority_gen(msgs, t[3]), t[3]) + "\n"
            response += "\n"
        await message.answer(response)
    else:
        await message.answer(msgs["viewtasksempty"])

# Отправка пользователю напоминания
async def send_reminder(id: int, user_id: int, task_text: str, deadline: str, category: str, priority: int, alerts_sent: int):
    pl = ""
    msgs = lang_ru()
    if alerts_sent == 0:
        pl = msgs["24hourless"]
    elif alerts_sent == 1:
        pl = msgs["12hourless"]
    elif alerts_sent == 2:
        pl = msgs["6hourless"]
    elif alerts_sent == 3:
        pl = msgs["2hourless"]
    elif alerts_sent == 4:
        pl = msgs["30minless"]
    
    text = msgs["remindertask"] % (deadline, priority_gen(msgs, priority), priority, category)

    if alerts_sent < 5:
        text = msgs["remindertoend"] % (task_text, id, pl)+"\n\n"+text
    else:
        text = msgs["reminderexpired"] % (task_text, id)+"\n\n"+text
    
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
    msgs = lang_ru()
    await message.answer(msgs["entertasktext"])
    await state.set_state(AddTaskStates.waiting_for_task_text)

# Получаем описание задачи
@dp.message(AddTaskStates.waiting_for_task_text)
async def process_task_text(message: types.Message, state: FSMContext):
    await state.update_data(task_text=message.text)
    msgs = lang_ru()
    await message.answer(msgs["enterdeadline"])
    await state.set_state(AddTaskStates.waiting_for_deadline)

# Получаем дедлайн задачи
@dp.message(AddTaskStates.waiting_for_deadline)
async def process_deadline(message: types.Message, state: FSMContext):
    msgs = lang_ru()
    try:
        deadline = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer(msgs["enterdeadlineerror"])
        return
    await state.update_data(deadline=deadline)
    await message.answer(msgs["entertaskcat"])
    await state.set_state(AddTaskStates.waiting_for_category)

# Получаем категорию задачи
@dp.message(AddTaskStates.waiting_for_category)
async def process_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    msgs = lang_ru()
    await message.answer(msgs["entertaskpri"])
    await state.set_state(AddTaskStates.waiting_for_priority)

# Получаем приоритет задачи
@dp.message(AddTaskStates.waiting_for_priority)
async def process_priority(message: types.Message, state: FSMContext):
    msgs = lang_ru()
    try:
        priority = int(message.text)
        if priority not in (1, 2, 3):
            raise ValueError
    except ValueError:
        await message.answer(msgs["entertaskprierror"])
        return

    await state.update_data(priority=priority)
    data = await state.get_data()

    # Определяем начальное значение alerts_sent
    now = datetime.now()
    time_diff = data['deadline'] - now
    if time_diff > timedelta(hours=24):
        alerts_sent = 0
        next = data['deadline'] - timedelta(hours=24)
    elif time_diff > timedelta(hours=12):
        alerts_sent = 1
        next = data['deadline'] - timedelta(hours=12)
    elif time_diff > timedelta(hours=6):
        alerts_sent = 2
        next = data['deadline'] - timedelta(hours=6)
    elif time_diff > timedelta(hours=2):
        alerts_sent = 3
        next = data['deadline'] - timedelta(hours=2)
    elif time_diff > timedelta(minutes=30):
        alerts_sent = 4
        next = data['deadline'] - timedelta(minutes=30)
    else:
        alerts_sent = 5
        next = data['deadline']

    # Вставка данных в базу
    async with db_session() as db:
        await db.execute('''INSERT INTO tasks (user_id, task_text, deadline, category, priority, alerts_sent, next_alert_at) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                            (message.from_user.id, data['task_text'], data['deadline'], data['category'], data['priority'], alerts_sent, next))
        await db.commit()

    await message.answer(msgs["taskadded"])
    await state.clear()

# Состояния завершения задачи для машины состояний
class CompleteTaskStates(StatesGroup):
    waiting_for_task_id = State()

@dp.message(Command("complete"))
async def complete_task_start(message: types.Message, state: FSMContext):
    msgs = lang_ru()
    await message.answer(msgs["entercompletetaskid"])
    await state.set_state(CompleteTaskStates.waiting_for_task_id)

@dp.message(CompleteTaskStates.waiting_for_task_id)
async def process_task_id(message: types.Message, state: FSMContext):
    msgs = lang_ru()
    try:
        task_id = int(message.text)
    except ValueError:
        await message.answer(msgs["entercompletetaskiderror"])
        return

    # Удаление задачи из базы данных
    async with db_session() as db:
        async with db.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, message.from_user.id)) as cursor:
            if cursor.rowcount == 0:  # Если строка не была найдена
                await message.answer(msgs["taskbyidnotfound"])
                return

        await db.commit()

    await message.answer(msgs["taskcompleted"])
    await state.clear()


# Обработчик простого текстового сообщения
@dp.message()
async def text_message_handler(message: types.Message, state: FSMContext):
    msgs = lang_ru()
    await message.answer(msgs["unknownmsg"])

async def main():
    await init_db()
    asyncio.create_task(reminder())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())