messages_ru = {
    "prilow": "Низкий 😇",
    "primedium": "Средний 😁",
    "prihigh": "Высокий 😤",
    "unknown": "(Неизвестно)",
    "viewtaskscat": "Категория \"%s\":",
    "viewtaskstask": "- Задача: %s (ID: %d)\n  Дедлайн: %s\n  Приоритет: %s (%d)",
    "viewtasksempty": "У вас <b>нет</b> задач.",
    "24hourless": "менее <b>24 часов</b>",
    "12hourless": "менее <b>12 часов</b>",
    "6hourless:" "менее <b>6 часов</b>",
    "2hourless:" "менее <b>2 часов</b> 🫢",
    "30minless": "менее <b>30 минут</b> 🫡",
    "remindertask": "\nДедлайн: %s\nПриоритет: %s (%d)\nКатегория: %s",
    "remindertoend": "До <b>завершения</b> дедлайна по задаче \"%s\" (ID: %d) осталось: <b>%s</b>!",
    "reminderexpired": "Задача \"%s\" (ID: %d) истекла 😰!!!",
    "entertasktext": "Введите текст задачи.",
    "enterdeadline": "Введите дедлайн задачи в формате 12.07.2024 12:30.",
    "enterdeadlineerror": "❌ Неверный формат даты. Введите в формате 12.07.2024 12:30.",
    "entertaskcat": "Введите категорию задачи.",
    "entertaskpri": "Введите приоритет задачи (1-3).",
    "entertaskprierror": "Приоритет должен быть числом от 1 до 3.",
    "taskadded": "Задача добавлена ✅",
    "entercompletetaskid": "Выберите задачу для завершения, отправив её ID.",
    "entercompletetaskiderror":"❌ Пожалуйста, введите корректный ID задачи.",
    "taskbyidnotfound": "❌ Задача с таким ID не найдена. Проверьте ID и попробуйте снова.",
    "taskcompleted": "Задача <b>успешно</b> завершена ✅",
    "unknownmsg": "Неизвестная команда. Введите /help для получения списка команд.",
    "helptext": (
        "Список доступных команд:\n"
        "/add - Добавить новую задачу\n"
        "/complete - Завершить задачу\n"
        "/tasks - Посмотреть все задачи\n"
        "/help - Показать это сообщение помощи\n"
        "\n"
        "/cancel - Отменить текущее действие\n"
    ),
    "canceled": "Действие отменено.",
    "cancelerror": "Никакого действия пока <b>не выбрано</b>!",
}

def l10n(lang: str):
    if lang == "ru":
        return messages_ru
    raise Exception(f"language not supported: {lang}")