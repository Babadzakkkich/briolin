from datetime import date
from typing import Optional


def calculate_age_from_birth_date(birth_date: date) -> int:
    """Рассчитывает возраст по дате рождения"""
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age