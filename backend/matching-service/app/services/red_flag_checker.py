import re
from typing import List, Tuple, Dict, Any, Optional

from app.core.logger import logger


class RedFlagChecker:
    """
    Проверка совместимости по Red Flags через прямое сопоставление с хобби.
    Red Flags сравниваются ТОЛЬКО с полем hobbies кандидата.
    """
    
    def __init__(self):
        pass  # Модель больше не нужна
    
    def _tokenize_hobbies(self, hobbies_text: str) -> List[str]:
        """Разбивает строку хобби на отдельные элементы"""
        if not hobbies_text:
            return []
        # Разбиваем по запятым, точкам, точкам с запятой, пробелам
        items = re.split(r'[,.;:\s]+', hobbies_text.lower().strip())
        return [item.strip() for item in items if len(item.strip()) >= 2]
    
    def _stem_word(self, word: str) -> str:
        """
        Простейший стемминг: отрезаем распространённые окончания.
        """
        suffixes = [
            'ешь', 'ете', 'етесь', 'ешься', 'ите', 'ишь', 'ять', 'ать',
            'еть', 'уть', 'оть', 'ыть', 'ти', 'ть', 'ся', 'сь',
            'ая', 'яя', 'ое', 'ее', 'ые', 'ие', 'ый', 'ий', 'ийся',
            'ого', 'его', 'ому', 'ему', 'ых', 'их', 'ую', 'юю',
            'а', 'я', 'о', 'е', 'ы', 'и', 'у', 'ю', 'ой', 'ей', 'ем', 'ом'
        ]
        
        word_lower = word.lower()
        for suffix in sorted(suffixes, key=len, reverse=True):
            if word_lower.endswith(suffix) and len(word_lower) - len(suffix) >= 3:
                return word_lower[:-len(suffix)]
        return word_lower
    
    def _check_text_match(self, red_flag: str, hobbies_text: str) -> Tuple[bool, str]:
        """
        Проверяет прямое совпадение red flag с хобби.
        """
        if not hobbies_text:
            return False, "Хобби не указаны"
        
        red_flag_normalized = red_flag.lower().strip()
        red_flag_stem = self._stem_word(red_flag_normalized)
        hobby_items = self._tokenize_hobbies(hobbies_text)
        
        # Сначала точное совпадение
        for hobby in hobby_items:
            if hobby == red_flag_normalized:
                return True, f"Точное совпадение: '{hobby}' = '{red_flag}'"
        
        # Затем совпадение по основе
        for hobby in hobby_items:
            hobby_stem = self._stem_word(hobby)
            if len(hobby_stem) >= 3 and len(red_flag_stem) >= 3:
                if hobby_stem == red_flag_stem:
                    return True, f"Совпадение по основе: '{hobby}' ≈ '{red_flag}'"
                if red_flag_stem in hobby_stem or hobby_stem in red_flag_stem:
                    return True, f"Частичное совпадение: '{hobby}' ∩ '{red_flag}'"
        
        return False, "Совпадений не найдено"
    
    async def check_red_flag_in_profile(
        self,
        red_flag: str,
        hobbies_text: str
    ) -> Tuple[bool, float, str]:
        """Проверка одного red flag"""
        is_conflict, reason = self._check_text_match(red_flag, hobbies_text)
        confidence = 1.0 if is_conflict else 0.0
        return is_conflict, confidence, reason
    
    async def is_profile_compatible(
        self,
        user_red_flags: List[str],
        candidate_hobbies_text: str
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Проверка всех red flags пользователя против хобби кандидата"""
        if not user_red_flags:
            return True, []
        
        checks = []
        is_compatible = True
        
        for red_flag in user_red_flags:
            if not red_flag or not red_flag.strip():
                continue
            
            is_conflict, confidence, reasoning = await self.check_red_flag_in_profile(
                red_flag, candidate_hobbies_text
            )
            
            check_result = {
                "red_flag": red_flag,
                "conflict": is_conflict,
                "confidence": round(confidence, 3),
                "reasoning": reasoning
            }
            checks.append(check_result)
            
            if is_conflict:
                is_compatible = False
                break
        
        return is_compatible, checks
    
    def get_profile_text(self, profile: Dict[str, Any]) -> str:
        """
        Возвращает ТОЛЬКО hobbies для проверки Red Flags.
        """
        detailed = profile.get("detailed") or {}
        return detailed.get("hobbies", "")


# Глобальный экземпляр
_red_flag_checker: Optional[RedFlagChecker] = None


def get_red_flag_checker() -> RedFlagChecker:
    global _red_flag_checker
    if _red_flag_checker is None:
        _red_flag_checker = RedFlagChecker()
    return _red_flag_checker