# stats.py - статистика и рекорды

import json
import os
from datetime import datetime

RECORDS_FILE = "records.json"
STATS_DIR = "stats"
LEADERBOARD_FILE = "leaderboard.json"


def load_records():
    if os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_records(records):
    with open(RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


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


def update_personal_record(user_id, score, streak):
    """Обновляет личный рекорд пользователя"""
    records = load_records()
    user_id_str = str(user_id)
    updated = False

    if user_id_str not in records:
        records[user_id_str] = {"best_score": 0, "max_streak": 0}

    if score > records[user_id_str].get("best_score", 0):
        records[user_id_str]["best_score"] = score
        updated = True

    if streak > records[user_id_str].get("max_streak", 0):
        records[user_id_str]["max_streak"] = streak
        updated = True

    if updated:
        save_records(records)

    return updated


def get_personal_record(user_id):
    """Возвращает личный рекорд пользователя"""
    records = load_records()
    user_id_str = str(user_id)
    if user_id_str in records:
        return records[user_id_str]
    return None