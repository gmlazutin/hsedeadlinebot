#Генерирует текстовое описание приоритета исходя из его численного значения
def priority_gen(pri: int) -> str:
    if pri == 1:
        return "Низкий"
    if pri == 2:
        return "Средний"
    if pri == 3:
        return "Высокий"
    return "<Неизвестно>"