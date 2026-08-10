from typing import Dict, List, Any
from datetime import datetime

from app.core.logger import logger
from app.database.mongo_models import Question, AnswerOption
from app.core.exceptions import InvalidAnswerException


class ScoringService:
    """Сервис для подсчета баллов теста"""
    
    async def calculate_total_score(
        self,
        questions: List[Question],
        user_answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Подсчет общего балла на основе ответов"""
        total_score = 0.0
        max_possible_score = 0.0
        answered_questions = 0
        
        logger.debug(f"Calculating score for {len(questions)} questions")
        
        for question in questions:
            question_id = question.id
            
            if question_id not in user_answers:
                logger.debug(f"No answer for question {question_id}")
                max_possible_for_question = await self._get_max_score_for_question(question)
                max_possible_score += max_possible_for_question
                continue
            
            answer_value = user_answers[question_id]
            
            question_score = 0.0
            max_score = 0.0
            
            if question.question_type == "multiple_choice":
                question_score, max_score = await self._process_multiple_choice(
                    question, answer_value
                )
            elif question.question_type == "likert_scale":
                question_score, max_score = await self._process_likert_scale(
                    question, answer_value
                )
            elif question.question_type == "true_false":
                question_score, max_score = await self._process_true_false(
                    question, answer_value
                )
            else:
                logger.warning(f"Unknown question type: {question.question_type}")
                question_score = 0.0
                max_score = await self._get_max_score_for_question(question)
            
            total_score += question_score
            max_possible_score += max_score
            answered_questions += 1
        
        # Нормализуем к 100-балльной шкале
        if max_possible_score > 0:
            normalized_percentage = (total_score / max_possible_score) * 100
        else:
            normalized_percentage = 0.0
        
        normalized_percentage = round(normalized_percentage, 2)
        total_score = round(total_score, 2)
        max_possible_score = round(max_possible_score, 2)
        
        passed = normalized_percentage >= 70.0
        
        logger.info(
            f"Test scoring complete: {total_score}/{max_possible_score} "
            f"({normalized_percentage}%) - {'PASSED' if passed else 'FAILED'}"
        )
        
        return {
            "total_score": total_score,
            "max_possible_score": max_possible_score,
            "percentage": normalized_percentage,
            "passed": passed,
            "answered_questions": answered_questions
        }
    
    async def _get_max_score_for_question(self, question: Question) -> float:
        """Получение максимального балла за вопрос"""
        if question.question_type == "multiple_choice":
            if question.options:
                return max(option.score for option in question.options)
        elif question.question_type == "likert_scale":
            return float(question.max_value or 5)
        elif question.question_type == "true_false":
            return 10.0
        
        return 10.0
    
    async def _process_multiple_choice(
        self,
        question: Question,
        answer_value: str
    ) -> tuple[float, float]:
        """Обработка ответов с множественным выбором"""
        selected_option = None
        
        for option in question.options:
            if option.id == answer_value:
                selected_option = option
                break
        
        if not selected_option:
            raise InvalidAnswerException(
                f"Invalid answer for question {question.id}: {answer_value}"
            )
        
        max_score = max(option.score for option in question.options)
        return selected_option.score, max_score
    
    async def _process_likert_scale(
        self,
        question: Question,
        answer_value: int
    ) -> tuple[float, float]:
        """Обработка ответов по шкале Лайкерта"""
        try:
            answer_int = int(answer_value)
            
            if question.min_value is None or question.max_value is None:
                logger.warning(f"Question {question.id} missing min_value or max_value")
                return 0.0, 10.0
            
            if not (question.min_value <= answer_int <= question.max_value):
                raise InvalidAnswerException(
                    f"Answer out of range for question {question.id}: {answer_int}"
                )
            
            min_val = question.min_value
            max_val = question.max_value
            
            if max_val == min_val:
                normalized_score = float(answer_int)
            else:
                normalized_score = ((answer_int - min_val) / (max_val - min_val)) * 10.0
            
            normalized_score = round(normalized_score, 2)
            
            return normalized_score, 10.0
            
        except (ValueError, TypeError) as e:
            raise InvalidAnswerException(
                f"Invalid answer format for question {question.id}: {e}"
            )
    
    async def _process_true_false(
        self,
        question: Question,
        answer_value: bool
    ) -> tuple[float, float]:
        """Обработка ответов true/false"""
        try:
            answer_bool = bool(answer_value)
            
            correct_option = next((opt for opt in question.options if opt.is_correct), None)
            
            if correct_option:
                score = 10.0 if answer_bool == correct_option.is_correct else 0.0
            else:
                score = 10.0 if answer_bool else 0.0
            
            return score, 10.0
            
        except (ValueError, TypeError):
            raise InvalidAnswerException(
                f"Invalid answer format for question {question.id}"
            )


_scoring_service = None

def get_scoring_service() -> ScoringService:
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service