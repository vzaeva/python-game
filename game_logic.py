# game_logic.py - игровая логика

import threading
import time
from config import TIME_LIMIT
from stats import save_user_stat, update_leaderboard, update_personal_record
from data import RULES, CATEGORIES
from keyboard import get_start_keyboard, get_menu_keyboard, get_back_keyboard, get_answer_keyboard
from utils import normalize_text


def start_hard_timer(user_id, players, send_keyboard_func, get_start_keyboard_func):
    """Запускает таймер на TIME_LIMIT секунд для сложного уровня"""

    def on_timeout():
        if user_id in players and players[user_id].get("step") == "playing_hard":
            if not players[user_id].get("answered_this", False):
                players[user_id]["timeout"] = True
                players[user_id]["answered_this"] = True
                save_user_stat(user_id, "Марафон (все категории)", "Сложный",
                               players[user_id]["correct"], players[user_id]["total"])
                send_keyboard_func(
                    user_id,
                    f"⏰ ВРЕМЯ ВЫШЛО! ⏰\n\n"
                    f"Ты не успел ответить на вопрос.\n\n"
                    f"🎮 ИГРА ОКОНЧЕНА!\n"
                    f"📊 Правильно: {players[user_id]['correct']} из {players[user_id]['total']}\n"
                    f"🔥 Серия: {players[user_id]['streak']}\n\n"
                    f"👇 Начни новую игру:",
                    get_start_keyboard_func()
                )
                players[user_id] = {"step": "menu"}

    timer = threading.Timer(TIME_LIMIT, on_timeout)
    timer.daemon = True
    timer.start()
    players[user_id]["timer"] = timer
    players[user_id]["answered_this"] = False
    players[user_id]["timeout"] = False


def check_easy_answer(user_id, players, user_answer, current_q, send_message_func, send_keyboard_func,
                      get_answer_keyboard_func, get_start_keyboard_func):
    """Проверяет ответ на лёгком уровне"""
    state = players[user_id]

    if normalize_text(user_answer) == normalize_text(current_q["correct"]):
        state["correct"] += 1
        state["index"] += 1
        state["streak"] += 1

        if state["index"] >= state["total"]:
            # Победа
            update_personal_record(user_id, state["correct"], state["streak"])
            save_user_stat(user_id, CATEGORIES[state["category"]], "Лёгкий", state["correct"], state["total"])
            update_leaderboard(user_id, state["correct"])

            send_keyboard_func(
                user_id,
                f"🌟 КАТЕГОРИЯ ПРОЙДЕНА! 🌟\n\n"
                f"📊 Результат: {state['correct']}/{state['total']}\n"
                f"🔥 Серия: {state['streak']}\n"
                f"⭐ Очки: {state['correct']}\n\n"
                f"👇 Начни новую игру:",
                get_start_keyboard_func()
            )
            players[user_id] = {"step": "menu"}
        else:
            send_message_func(user_id, "✅ ВЕРНО!")
            q = state["questions"][state["index"]]
            state["current_q"] = q
            send_keyboard_func(
                user_id,
                f"📝 ВОПРОС {state['index'] + 1}/{state['total']}\n🔥 Серия: {state['streak']}\n\n{q['question']}",
                get_answer_keyboard_func(q['options'])
            )
    else:
        # Неправильный ответ
        rule = RULES.get(state["category"], "Правило не найдено")
        save_user_stat(user_id, CATEGORIES[state["category"]], "Лёгкий", state["correct"], state["total"])

        send_keyboard_func(
            user_id,
            f"❌ НЕПРАВИЛЬНО!\n\n"
            f"📝 Твой ответ: {user_answer}\n"
            f"✅ Правильный: {current_q['correct']}\n\n"
            f"{rule}\n\n"
            f"🎮 ИГРА ОКОНЧЕНА!\n"
            f"📊 Правильно: {state['correct']} из {state['total']}\n"
            f"🔥 Серия: {state['streak']}\n\n"
            f"👇 Начни новую игру:",
            get_start_keyboard_func()
        )
        players[user_id] = {"step": "menu"}


def check_hard_answer(user_id, players, user_answer, current_q, send_message_func, send_keyboard_func,
                      get_start_keyboard_func, get_back_keyboard_func, start_hard_timer_func):
    """Проверяет ответ на сложном уровне"""
    state = players[user_id]

    # Отменяем текущий таймер
    if state.get("timer"):
        try:
            state["timer"].cancel()
        except:
            pass

    if normalize_text(user_answer.strip()) == normalize_text(current_q["correct"]):
        state["correct"] += 1
        state["index"] += 1
        state["streak"] += 1

        if state["index"] >= state["total"]:
            # Победа
            update_personal_record(user_id, state["correct"], state["streak"])
            save_user_stat(user_id, "Марафон (все категории)", "Сложный", state["correct"], state["total"])
            update_leaderboard(user_id, state["correct"])

            send_keyboard_func(
                user_id,
                f"🌟 МАРАФОН ПРОЙДЕН! 🌟\n\n"
                f"📊 Результат: {state['correct']}/{state['total']}\n"
                f"🔥 Серия: {state['streak']}\n"
                f"⭐ Очки: {state['correct']}\n\n"
                f"👇 Начни новую игру:",
                get_start_keyboard_func()
            )
            players[user_id] = {"step": "menu"}
        else:
            send_message_func(user_id, f"✅ ВЕРНО! Правильно: {current_q['correct']}")
            q = state["questions"][state["index"]]
            state["current_q"] = q
            state["answered_this"] = False

            send_keyboard_func(
                user_id,
                f"📝 ВОПРОС {state['index'] + 1}/{state['total']}\n"
                f"🔥 Серия: {state['streak']}\n"
                f"⏱️ У тебя {TIME_LIMIT} СЕКУНД!\n\n"
                f"❌ Слово с ошибкой: {q['wrong']}\n\n"
                f"✏️ Напиши правильный вариант:",
                get_back_keyboard_func()
            )
            start_hard_timer_func(user_id)
    else:
        # Неправильный ответ
        rule = RULES.get(current_q.get("rule", "лаг_лож"), "Правило не найдено")
        hint = current_q.get("hint", "")
        save_user_stat(user_id, "Марафон (все категории)", "Сложный", state["correct"], state["total"])

        send_keyboard_func(
            user_id,
            f"❌ НЕПРАВИЛЬНО!\n\n"
            f"📝 Твой ответ: {user_answer}\n"
            f"✅ Правильный: {current_q['correct']}\n\n"
            f"💡 Подсказка: {hint}\n\n"
            f"{rule}\n\n"
            f"🎮 ИГРА ОКОНЧЕНА!\n"
            f"📊 Правильно: {state['correct']} из {state['total']}\n"
            f"🔥 Серия: {state['streak']}\n\n"
            f"👇 Начни новую игру:",
            get_start_keyboard_func()
        )
        players[user_id] = {"step": "menu"}