import aiosqlite

# Создание сеанса доступа к бд
def db_session():
    return aiosqlite.connect('main.db')

# Инициализация базы данных
async def init_db():
    async with db_session() as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS tasks (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL,
                                task_text TEXT NOT NULL,
                                deadline DATETIME NOT NULL,
                                category TEXT,
                                priority INTEGER DEFAULT 1,
                                alerts_sent INTEGER DEFAULT 0
                            )''')
        await db.commit()

#таблица tasks:
#id - уникальный id задачи
#user_id - айди пользователя, который создал задачу (telegram id)
#task_text - непосредственно сама задача
#deadline - время дедлайна для задачи
#category - категория задачи (в данный момент - обычное текстовое поле)
#priority - приоритет (по-умолчанию 1, всего планируется 3 уровня важности на данный момент)
#alerts_sent - количество посланных пользователю уведомлений. По этому параметру бот должен будет понимать,
#              сколько ещё уведомлений должен получить пользователь о задаче (в данный момент время получения
#              уведов фиксировано, добавлять возможность его редактирования пока что не планируется)