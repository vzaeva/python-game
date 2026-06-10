# bot.py - главный файл

import random
import json
import os
import threading
from datetime import datetime
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from data import RULES, QUESTIONS_EASY, QUESTIONS_HARD, CATEGORIES
from keyboard import (
    get_start_keyboard, get_difficulty_keyboard, get_categories_keyboard,
    get_answer_keyboard, get_menu_keyboard
)

TOKEN = "vk1.a.1DAS8SdvMsTNS92nuK9J5e9XumYLugGaIdahm3xjo25amjFqoUwmzVtIE1QPPqjM6R408fxb-o8_xFEzdQdtxZqZRdDSsw_F75ommctDemrQzzpeeGttxPNsWLG-4NLyb6Iu1nhI5CPtLjlVuWqTRDTtVtGNH6PxQfRod_eCu00LpQDJa3yaPMao-2XHwvbiOq0W1PooeD4h6d60eBwi7Q"
GROUP_ID = 238701001

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

players = {}
RECORDS_FILE = "records.json"
STATS_DIR = "stats"
LEADERBOARD_FILE = "leaderboard.json"
TIME_LIMIT = 15


def normalize_text(s):
    """Заменяет е на ё и приводит к нижнему регистру"""
    return s.lower().replace('е', 'ё')


def load_records():
    if os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_records(records):
    with open(RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def save_user_stat(user_id, category, difficulty, score, total):
    """Сохраняет статистику игры (всегда, даже если игра не пройдена)"""
    if not os.path.exists(STATS_DIR):
        os.makedirs(STATS_DIR)

    file_path = os.path.join(STATS_DIR, f"{user_id}.json")

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            stats = json.load(f)
    else:
        stats = {"games": [], "total_score": 0, "games_count": 0}

    stats["games"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": category,
        "difficulty": difficulty,
        "score": score,
        "total": total
    })
    stats["total_score"] += score
    stats["games_count"] += 1

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_leaderboard(leaderboard):
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(leaderboard, f, ensure_ascii=False, indent=2)


def update_leaderboard(user_id, score):
    """Обновляет таблицу лидеров (суммирует все очки пользователя)"""
    leaderboard = load_leaderboard()

    user_id_str = str(user_id)
    if user_id_str not in leaderboard:
        leaderboard[user_id_str] = 0
    leaderboard[user_id_str] += score
    save_leaderboard(leaderboard)
    return True


def get_top_players(limit=10):
    """Возвращает топ-N игроков с их именами и ОБЩИМ количеством очков"""
    leaderboard = load_leaderboard()

    if not leaderboard:
        return None

    sorted_players = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)[:limit]

    top_list = []
    for i, (user_id, total_score) in enumerate(sorted_players, 1):
        try:
            user_info = vk.users.get(user_ids=int(user_id))
            name = f"{user_info[0]['first_name']} {user_info[0]['last_name']}"
        except:
            name = f"Пользователь {user_id}"
        top_list.append((i, name, total_score))

    return top_list


def send_message(user_id, text):
    vk.messages.send(user_id=user_id, message=text, random_id=0)


def send_keyboard(user_id, text, keyboard):
    vk.messages.send(
        user_id=user_id,
        message=text,
        random_id=0,
        keyboard=keyboard.get_keyboard()
    )


def start_hard_timer(user_id):
    """Запускает таймер на TIME_LIMIT секунд для сложного уровня"""
    state = players.get(user_id)
    if not state or state.get("step") != "playing_hard":
        return

    old_timer = state.get("timer")
    if old_timer:
        try:
            old_timer.cancel()
        except:
            pass

    def on_timeout():
        current = players.get(user_id)
        if not current or current.get("step") != "playing_hard":
            return
        if current.get("answered_this", False):
            return

        current["timeout"] = True
        current["answered_this"] = True

        # Сохраняем статистику при таймауте
        save_user_stat(user_id, "Марафон (все категории)", "Сложный", current["correct"], current["total"])
        # Обновляем таблицу лидеров (сколько успел набрать)
        update_leaderboard(user_id, current["correct"])

        send_keyboard(
            user_id,
            f"⏰ ВРЕМЯ ВЫШЛО! ⏰\n\n"
            f"Ты не успел ответить на вопрос.\n\n"
            f"🎮 ИГРА ОКОНЧЕНА!\n"
            f"📊 Правильно: {current['correct']} из {current['total']}\n"
            f"🔥 Серия: {current['streak']}\n\n"
            f"👇 Начни новую игру:",
            get_start_keyboard()
        )
        players[user_id] = {"step": "menu"}

    timer = threading.Timer(TIME_LIMIT, on_timeout)
    timer.daemon = True
    timer.start()
    state["timer"] = timer
    state["answered_this"] = False
    state["timeout"] = False


print("🤖 VK Бот запущен!")
print(f"📚 Загружено категорий: {len(CATEGORIES)}")
print(f"⏱️ Таймер на сложном уровне: {TIME_LIMIT} секунд на каждый вопрос")
print("📌 Напиши /start в сообщения сообщества")

for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
        user_id = event.message['from_id']
        text = event.message['text'].strip()

        if user_id not in players:
            players[user_id] = {"step": "menu"}

        state = players[user_id]

        # ========== ГЛАВНОЕ МЕНЮ ==========
        if text == "/start":
            players[user_id] = {"step": "menu"}

            try:
                user_info = vk.users.get(user_ids=user_id)
                user_name = user_info[0]['first_name']
            except:
                user_name = "друг"

            send_keyboard(
                user_id,
                f"🎓 Привет, {user_name}!\n\n"
                f"📌 ИГРА «ГРАМОТЕЙ»\n\n"
                f"📖 *Как играть:*\n"
                f"• Выбери уровень сложности\n"
                f"• Отвечай на вопросы\n"
                f"• При ошибке бот покажет правило\n\n"
                f"🟢 Лёгкий — выбор из 2 кнопок\n"
                f"🔴 Сложный — найди ошибку + таймер {TIME_LIMIT} сек\n\n"
                f"👇 Выбери действие:",
                get_start_keyboard()
            )
            continue

        if text == "◀️ В главное меню":
            if state.get("timer"):
                try:
                    state["timer"].cancel()
                except:
                    pass
            players[user_id] = {"step": "menu"}
            send_keyboard(user_id, "👇 Выбери действие:", get_start_keyboard())
            continue

        if state["step"] == "menu":
            if text == "🎮 Начать игру":
                players[user_id] = {"step": "difficulty"}
                send_keyboard(user_id, "🎮 ВЫБЕРИ УРОВЕНЬ СЛОЖНОСТИ:", get_difficulty_keyboard())
                continue

            elif text == "📊 Моя статистика":
                file_path = os.path.join(STATS_DIR, f"{user_id}.json")
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        stats = json.load(f)
                    last_game = stats["games"][-1] if stats["games"] else None
                    msg = f"📊 ТВОЯ СТАТИСТИКА 📊\n\n🎮 Всего игр: {stats['games_count']}\n⭐ Всего очков: {stats['total_score']}\n"
                    if stats['games_count'] > 0:
                        msg += f"📈 Средний результат: {stats['total_score'] // stats['games_count']}\n"
                    if last_game:
                        msg += f"\n📅 Последняя игра:\n{last_game['category']} | {last_game['score']}/{last_game['total']} | {last_game['difficulty']}"
                    send_keyboard(user_id, msg + "\n\n⬅️ Нажми кнопку, чтобы вернуться:", get_menu_keyboard())
                else:
                    send_keyboard(
                        user_id,
                        "📊 У тебя пока нет сохранённых игр.\nСыграй, чтобы появилась статистика!\n\n⬅️ Нажми кнопку, чтобы вернуться:",
                        get_menu_keyboard()
                    )
                continue

            elif text == "🏅 Таблица лидеров":
                top_players = get_top_players(10)
                if top_players:
                    msg = "🏅 *ТАБЛИЦА ЛИДЕРОВ* 🏅\n\n"
                    for place, name, total_score in top_players:
                        medal = ""
                        if place == 1:
                            medal = "🥇 "
                        elif place == 2:
                            medal = "🥈 "
                        elif place == 3:
                            medal = "🥉 "
                        msg += f"{medal}{place}. {name} — {total_score} очков\n"
                    send_keyboard(user_id, msg, get_menu_keyboard())
                else:
                    send_keyboard(user_id, "🏅 Пока нет рекордов! Стань первым!", get_menu_keyboard())
                continue

            else:
                send_keyboard(user_id, "❓ Напиши /start или выбери действие:", get_start_keyboard())
                continue

        # ========== ВЫБОР СЛОЖНОСТИ ==========
        if state["step"] == "difficulty":
            if "Лёгкий" in text:
                players[user_id] = {"step": "category", "difficulty": "easy"}
                send_keyboard(user_id, "📚 ВЫБЕРИ КАТЕГОРИЮ:", get_categories_keyboard())
                continue
            elif "Сложный" in text:
                questions = QUESTIONS_HARD.copy()
                random.shuffle(questions)
                players[user_id] = {
                    "step": "playing_hard",
                    "difficulty": "hard",
                    "questions": questions,
                    "index": 0,
                    "correct": 0,
                    "total": len(questions),
                    "streak": 0,
                    "answered_this": False,
                    "timeout": False,
                    "timer": None
                }
                q = questions[0]
                players[user_id]["current_q"] = q

                send_keyboard(
                    user_id,
                    f"🔴 СЛОЖНЫЙ УРОВЕНЬ 🔴\n\n"
                    f"📌 Режим: «Найди ошибку»\n"
                    f"📊 Всего вопросов: {len(questions)}\n"
                    f"⏱️ На каждый вопрос даётся {TIME_LIMIT} секунд!\n\n"
                    f"📝 ВОПРОС 1/{len(questions)}:\n\n"
                    f"❌ Слово с ошибкой: *{q['wrong']}*\n\n"
                    f"✏️ Напиши правильный вариант:",
                    get_menu_keyboard()
                )
                start_hard_timer(user_id)
                continue
            elif text == "◀️ Назад":
                players[user_id] = {"step": "menu"}
                send_keyboard(user_id, "👇 Выбери действие:", get_start_keyboard())
                continue
            else:
                send_keyboard(user_id, "❓ Выбери уровень сложности:", get_difficulty_keyboard())
                continue

        # ========== ВЫБОР КАТЕГОРИИ (ЛЁГКИЙ УРОВЕНЬ) ==========
        if state["step"] == "category":
            if text == "◀️ Назад":
                players[user_id] = {"step": "difficulty"}
                send_keyboard(user_id, "🎮 Выбери уровень сложности:", get_difficulty_keyboard())
                continue

            category = None
            for key, name in CATEGORIES.items():
                if text == name:
                    category = key
                    break

            if category:
                questions = QUESTIONS_EASY[category].copy()
                random.shuffle(questions)
                players[user_id] = {
                    "step": "playing_easy",
                    "difficulty": "easy",
                    "category": category,
                    "questions": questions,
                    "index": 0,
                    "correct": 0,
                    "total": len(questions),
                    "streak": 0
                }
                q = questions[0]
                players[user_id]["current_q"] = q
                send_keyboard(
                    user_id,
                    f"✅ Категория: {CATEGORIES[category]}\n"
                    f"📊 Вопросов: {len(questions)}\n"
                    f"🟢 УРОВЕНЬ: ЛЁГКИЙ\n\n"
                    f"📝 ВОПРОС 1/{len(questions)}:\n\n{q['question']}",
                    get_answer_keyboard(q['options'])
                )
            else:
                send_keyboard(user_id, "❓ Выбери категорию из кнопок:", get_categories_keyboard())
            continue

        # ========== ЛЁГКИЙ УРОВЕНЬ - ИГРА ==========
        if state["step"] == "playing_easy":
            if text == "◀️ Выйти в меню":
                players[user_id] = {"step": "menu"}
                send_keyboard(user_id, "👇 Выбери действие:", get_start_keyboard())
                continue

            current_q = state.get("current_q")
            if not current_q:
                send_message(user_id, "Ошибка. Напиши /start")
                continue

            if normalize_text(text) == normalize_text(current_q["correct"]):
                state["correct"] += 1
                state["index"] += 1
                state["streak"] += 1

                if state["index"] >= state["total"]:
                    # Обновляем личный рекорд
                    records = load_records()
                    if str(user_id) not in records or state["correct"] > records[str(user_id)].get("best_score", 0):
                        if str(user_id) not in records:
                            records[str(user_id)] = {}
                        records[str(user_id)]["best_score"] = state["correct"]
                        records[str(user_id)]["max_streak"] = max(state["streak"],
                                                                  records[str(user_id)].get("max_streak", 0))
                        save_records(records)
                        send_message(user_id,
                                     f"🏆 НОВЫЙ РЕКОРД! 🏆\n{state['correct']} очков!\n🔥 Серия: {state['streak']}")

                    # Сохраняем статистику игры (ПОБЕДА)
                    save_user_stat(user_id, CATEGORIES[state["category"]], "Лёгкий", state["correct"], state["total"])

                    # Обновляем таблицу лидеров (суммируем очки)
                    update_leaderboard(user_id, state["correct"])

                    send_keyboard(
                        user_id,
                        f"🌟 КАТЕГОРИЯ ПРОЙДЕНА! 🌟\n\n"
                        f"📊 Результат: {state['correct']}/{state['total']}\n"
                        f"🔥 Серия: {state['streak']}\n"
                        f"⭐ Очки: {state['correct']}\n\n"
                        f"👇 Начни новую игру:",
                        get_start_keyboard()
                    )
                    players[user_id] = {"step": "menu"}
                else:
                    send_message(user_id, "✅ ВЕРНО!")
                    q = state["questions"][state["index"]]
                    state["current_q"] = q
                    send_keyboard(
                        user_id,
                        f"📝 ВОПРОС {state['index'] + 1}/{state['total']}\n🔥 Серия: {state['streak']}\n\n{q['question']}",
                        get_answer_keyboard(q['options'])
                    )
            else:
                rule = RULES.get(state["category"], "Правило не найдено")

                # Сохраняем статистику ДАЖЕ ПРИ ОШИБКЕ
                save_user_stat(user_id, CATEGORIES[state["category"]], "Лёгкий", state["correct"], state["total"])
                # Обновляем таблицу лидеров (сколько успел набрать)
                update_leaderboard(user_id, state["correct"])

                send_keyboard(
                    user_id,
                    f"❌ НЕПРАВИЛЬНО!\n\n"
                    f"📝 Твой ответ: {text}\n"
                    f"✅ Правильный: {current_q['correct']}\n\n"
                    f"{rule}\n\n"
                    f"🎮 ИГРА ОКОНЧЕНА!\n"
                    f"📊 Правильно: {state['correct']} из {state['total']}\n"
                    f"🔥 Серия: {state['streak']}\n\n"
                    f"👇 Начни новую игру:",
                    get_start_keyboard()
                )
                players[user_id] = {"step": "menu"}
            continue

        # ========== СЛОЖНЫЙ УРОВЕНЬ - ИГРА ==========
        if state["step"] == "playing_hard":
            if text == "◀️ Выйти в меню":
                if state.get("timer"):
                    try:
                        state["timer"].cancel()
                    except:
                        pass
                players[user_id] = {"step": "menu"}
                send_keyboard(user_id, "👇 Выбери действие:", get_start_keyboard())
                continue

            if state.get("timeout", False):
                send_message(user_id, "⏰ Время на этот вопрос вышло! Игра окончена. Напиши /start")
                continue

            if state.get("answered_this", False):
                send_message(user_id, "Ты уже ответил на этот вопрос!")
                continue

            current_q = state.get("current_q")
            if not current_q:
                send_message(user_id, "Ошибка. Напиши /start")
                continue

            state["answered_this"] = True

            if state.get("timer"):
                try:
                    state["timer"].cancel()
                except:
                    pass

            if normalize_text(text.strip()) == normalize_text(current_q["correct"]):
                state["correct"] += 1
                state["index"] += 1
                state["streak"] += 1

                if state["index"] >= state["total"]:
                    # Обновляем личный рекорд
                    records = load_records()
                    if str(user_id) not in records or state["correct"] > records[str(user_id)].get("best_score", 0):
                        if str(user_id) not in records:
                            records[str(user_id)] = {}
                        records[str(user_id)]["best_score"] = state["correct"]
                        records[str(user_id)]["max_streak"] = max(state["streak"],
                                                                  records[str(user_id)].get("max_streak", 0))
                        save_records(records)
                        send_message(user_id,
                                     f"🏆 НОВЫЙ РЕКОРД! 🏆\n{state['correct']} очков!\n🔥 Серия: {state['streak']}")

                    # Сохраняем статистику игры (ПОБЕДА)
                    save_user_stat(user_id, "Марафон (все категории)", "Сложный", state["correct"], state["total"])

                    # Обновляем таблицу лидеров (суммируем очки)
                    update_leaderboard(user_id, state["correct"])

                    send_keyboard(
                        user_id,
                        f"🌟 МАРАФОН ПРОЙДЕН! 🌟\n\n"
                        f"📊 Результат: {state['correct']}/{state['total']}\n"
                        f"🔥 Серия: {state['streak']}\n"
                        f"⭐ Очки: {state['correct']}\n\n"
                        f"👇 Начни новую игру:",
                        get_start_keyboard()
                    )
                    players[user_id] = {"step": "menu"}
                else:
                    send_message(user_id, f"✅ ВЕРНО! Правильно: {current_q['correct']}")

                    q = state["questions"][state["index"]]
                    state["current_q"] = q

                    send_keyboard(
                        user_id,
                        f"📝 ВОПРОС {state['index'] + 1}/{state['total']}\n"
                        f"🔥 Серия: {state['streak']}\n"
                        f"⏱️ У тебя {TIME_LIMIT} СЕКУНД!\n\n"
                        f"❌ Слово с ошибкой: *{q['wrong']}*\n\n"
                        f"✏️ Напиши правильный вариант:",
                        get_menu_keyboard()
                    )
                    start_hard_timer(user_id)
            else:
                rule = RULES.get(current_q.get("rule", "лаг_лож"), "Правило не найдено")
                hint = current_q.get("hint", "")

                # Сохраняем статистику ДАЖЕ ПРИ ОШИБКЕ
                save_user_stat(user_id, "Марафон (все категории)", "Сложный", state["correct"], state["total"])
                # Обновляем таблицу лидеров (сколько успел набрать)
                update_leaderboard(user_id, state["correct"])

                send_keyboard(
                    user_id,
                    f"❌ НЕПРАВИЛЬНО!\n\n"
                    f"📝 Твой ответ: {text}\n"
                    f"✅ Правильный: {current_q['correct']}\n\n"
                    f"💡 Подсказка: {hint}\n\n"
                    f"{rule}\n\n"
                    f"🎮 ИГРА ОКОНЧЕНА!\n"
                    f"📊 Правильно: {state['correct']} из {state['total']}\n"
                    f"🔥 Серия: {state['streak']}\n\n"
                    f"👇 Начни новую игру:",
                    get_start_keyboard()
                )
                players[user_id] = {"step": "menu"}
            continue

        send_message(user_id, "Напиши /start")