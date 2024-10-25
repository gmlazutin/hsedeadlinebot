messages_ru = {
    "prilow": "Низкий",
    "primedium": "Средний",
    "prihigh": "Высокий",
    "unknown": "<Неизвестно>",
    "viewtaskscat": "Категория \"%s\":",
    "viewtaskstask": "- Задача: %s (ID: %d)\n  Дедлайн: %s\n  Приоритет: %s (%d)",
    "viewtasksempty": "У вас нет задач.",
    "24hourless": "менее 24 часов",
    "12hourless": "менее 12 часов",
    "6hourless": "менее 6 часов",
    "2hourless": "менее 2 часов",
    "30minless": "менее 30 минут",
    "remindertask": "\nДедлайн: %s\nПриоритет: %s (%d)\nКатегория: %s",
    "remindertoend": "До завершения дедлайна по задаче \"%s\" (ID: %d) осталось: %s!",
    "reminderexpired": "Задача \"%s\" (ID: %d) истекла!!!",
    "entertasktext": "Введите текст задачи.",
    "enterdeadline": "Введите дедлайн задачи в формате 12.07.2024 12:30.",
    "enterdeadlineerror": "Неверный формат даты. Введите в формате 12.07.2024 12:30.",
    "entertaskcat": "Введите категорию задачи.",
    "entertaskpri": "Введите приоритет задачи (1-3).",
    "entertaskprierror": "Приоритет должен быть числом от 1 до 3.",
    "taskadded": "Задача добавлена!",
    "entercompletetaskid": "Выберите задачу для завершения, отправив её ID.",
    "entercompletetaskiderror":"Пожалуйста, введите корректный ID задачи.",
    "taskbyidnotfound": "Задача с таким ID не найдена. Проверьте ID и попробуйте снова.",
    "taskcompleted": "Задача успешно завершена!",
    "unknownmsg": "Неизвестная команда. Введите /help для получения списка команд.",
    "helptext": (
        "Список доступных команд:\n"
        "/add - Добавить новую задачу\n"
        "/complete - Завершить задачу\n"
        "/tasks - Посмотреть все задачи\n"
        "/help - Показать это сообщение помощи\n"
    ),
}

def l10n(lang: str):
    if lang == "ru":
        return messages_ru
    raise Exception(f"language not supported: {lang}")