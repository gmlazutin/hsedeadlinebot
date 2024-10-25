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
                                alerts_sent INTEGER DEFAULT 0,
                                next_alert_at DATETIME,
                                created_at DATETIME NOT NULL
                            )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS stats (
                                id INTEGER PRIMARY KEY,
                                user_id INTEGER NOT NULL,
                                deadline DATETIME NOT NULL,
                                completed INTEGER DEFAULT 0,
                                created_at DATETIME NOT NULL
                         )''')
        await db.commit()

#Таблица tasks:
#id - уникальный id задачи
#user_id - айди пользователя, который создал задачу (telegram id)
#task_text - непосредственно сама задача
#deadline - время дедлайна для задачи
#category - категория задачи (в данный момент - обычное текстовое поле)
#priority - приоритет (по-умолчанию 1, всего планируется 3 уровня важности на данный момент)
#alerts_sent - количество посланных пользователю уведомлений. По этому параметру бот должен будет понимать,
#              сколько ещё уведомлений должен получить пользователь о задаче (в данный момент время получения
#              уведов фиксировано (5), добавлять возможность его редактирования пока что не планируется). В случае,
#              если данный параметр равен 6, бот должен приравнять next_alert_at к deadline.
#next_alert_at - время, в которое должен пользователь получить следующее уведомление.

#Логика работы с alerts_send и next_alert_at:
#По-умолчанию alerts_sent равен нулю, в случае, если до дедлайна задачи больше суток. Если меньше суток, то
#при создании записи в таблице назначается 1. Если меньше 12 часов, то 2. Если меньше 6 часов, то 3. Если меньше 2 часов, то 4. 
#Если меньше 30 минут, то 5.
#Аналогичная логика применяется при SELECT-е строк таблицы, в которых next_alert_at >= time_now. 