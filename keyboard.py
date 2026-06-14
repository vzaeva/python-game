# keyboard.py - клавиатуры

from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from data import CATEGORIES


def get_start_keyboard():
    """Главное меню"""
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("🎮 Начать игру", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("📊 Моя статистика", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("🏅 Таблица лидеров", color=VkKeyboardColor.PRIMARY)
    return keyboard


def get_difficulty_keyboard():
    """Выбор уровня сложности"""
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("🟢 Лёгкий", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("🔴 Сложный", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("◀️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard


def get_categories_keyboard():
    """Клавиатура выбора категории (3 кнопки в строке)"""
    keyboard = VkKeyboard(one_time=True)

    cats = list(CATEGORIES.values())
    row = []
    for i, cat in enumerate(cats):
        row.append(cat)
        if len(row) == 3 or i == len(cats) - 1:
            for btn in row:
                keyboard.add_button(btn, color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            row = []

    keyboard.add_button("◀️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard


def get_answer_keyboard(options):
    """Клавиатура для ответов на лёгком уровне"""
    keyboard = VkKeyboard(one_time=True)
    for opt in options:
        keyboard.add_button(opt, color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("◀️ Выйти в меню", color=VkKeyboardColor.SECONDARY)
    return keyboard


def get_menu_keyboard():
    """Клавиатура для возврата в меню"""
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("◀️ В главное меню", color=VkKeyboardColor.SECONDARY)
    return keyboard


def get_back_keyboard():
    """Клавиатура с кнопкой выхода (для сложного уровня)"""
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("◀️ Выйти в меню", color=VkKeyboardColor.SECONDARY)
    return keyboard