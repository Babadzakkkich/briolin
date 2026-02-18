from datetime import date
from typing import Optional


def calculate_age(birth_date: date) -> int:
    """Рассчитывает возраст по дате рождения"""
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age


def get_age_condition(min_age: Optional[int] = None, max_age: Optional[int] = None) -> str:
    """Возвращает SQL условие для фильтрации по возрасту"""
    conditions = []

    if min_age is not None:
        conditions.append(f"EXTRACT(YEAR FROM age(date_of_birth)) >= {min_age}")

    if max_age is not None:
        conditions.append(f"EXTRACT(YEAR FROM age(date_of_birth)) <= {max_age}")

    return " AND ".join(conditions) if conditions else "1=1"