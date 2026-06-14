# utils.py - вспомогательные функции

def normalize_text(s):
    """Заменяет е на ё и приводит к нижнему регистру"""
    return s.lower().replace('е', 'ё')