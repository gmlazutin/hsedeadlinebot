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
