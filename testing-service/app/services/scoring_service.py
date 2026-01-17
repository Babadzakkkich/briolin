from typing import Dict, List, Tuple, Any
from datetime import datetime

from app.core.logger import logger
from app.database.mongo_models import Question, AnswerOption, PersonalityDimension
from app.database.models import PersonalityType
from app.core.exceptions import InvalidAnswerException


class ScoringService:
    """Сервис для подсчета баллов и определения типа личности"""
    
    async def calculate_scores(
        self,
        questions: List[Question],
        user_answers: Dict[str, Any]
    ) -> Dict[PersonalityDimension, float]:
        """Подсчет баллов по типам личности на основе ответов"""
        scores = {dimension: 0.0 for dimension in PersonalityDimension}
        
        logger.debug(f"Calculating scores for {len(questions)} questions")
        
        for i, question in enumerate(questions):
            question_id = question.id
            
            if question_id not in user_answers:
                logger.warning(f"No answer for question {question_id}")
                continue
            
            answer_value = user_answers[question_id]
            
            # Обработка в зависимости от типа вопроса
            if question.question_type == "multiple_choice":
                await self._process_multiple_choice(
                    question, answer_value, scores
                )
            elif question.question_type == "likert_scale":
                # Проверяем перед обработкой
                if question.min_value is None or question.max_value is None:
                    logger.error(f"Question {question_id} (likert_scale) missing min_value or max_value")
                    continue
                await self._process_likert_scale(
                    question, answer_value, scores
                )
            elif question.question_type == "true_false":
                await self._process_true_false(
                    question, answer_value, scores
                )
            else:
                logger.warning(f"Unknown question type: {question.question_type}")
        
        logger.debug(f"Final scores: {scores}")
        return scores
    
    async def _process_multiple_choice(
        self,
        question: Question,
        answer_value: str,
        scores: Dict[PersonalityDimension, float]
    ):
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
        
        # Добавляем баллы из score_impact
        if hasattr(selected_option, 'score_impact') and selected_option.score_impact:
            for dimension_name, impact in selected_option.score_impact.items():
                try:
                    # Проверяем, что dimension_name - это строка, а не объект PersonalityDimension
                    if isinstance(dimension_name, PersonalityDimension):
                        dimension = dimension_name
                    else:
                        dimension = PersonalityDimension(dimension_name)
                    if dimension in scores:
                        scores[dimension] += impact
                except ValueError:
                    # Пропускаем неизвестные измерения
                    continue
    
    async def _process_likert_scale(
        self,
        question: Question,
        answer_value: int,
        scores: Dict[PersonalityDimension, float]
    ):
        """Обработка ответов по шкале Лайкерта"""
        try:
            # Проверяем, что у вопроса есть min_value и max_value
            if question.min_value is None or question.max_value is None:
                logger.warning(f"Question {question.id} missing min_value or max_value")
                return
            
            answer_int = int(answer_value)
            
            # Проверяем, что ответ в пределах диапазона
            if not (question.min_value <= answer_int <= question.max_value):
                raise InvalidAnswerException(
                    f"Answer out of range for question {question.id}: {answer_int}. "
                    f"Expected between {question.min_value} and {question.max_value}"
                )
            
            # Нормализуем значение от 0 до 1
            normalized = (answer_int - question.min_value) / (question.max_value - question.min_value)
            
            # Распределяем по типам личности, измеряемым вопросом
            if question.personality_dimensions:
                for dimension_name in question.personality_dimensions:
                    try:
                        if isinstance(dimension_name, PersonalityDimension):
                            dimension = dimension_name
                        else:
                            dimension = PersonalityDimension(dimension_name)
                        if dimension in scores:
                            scores[dimension] += normalized * 2
                    except ValueError:
                        logger.warning(f"Unknown personality dimension: {dimension_name} in question {question.id}")
                        continue
            
        except (ValueError, TypeError) as e:
            raise InvalidAnswerException(
                f"Invalid answer format for question {question.id}: {e}"
            )
    
    async def _process_true_false(
        self,
        question: Question,
        answer_value: bool,
        scores: Dict[PersonalityDimension, float]
    ):
        """Обработка ответов true/false"""
        try:
            answer_bool = bool(answer_value)
            
            # Простая логика: true добавляет баллы, false не добавляет
            if answer_bool:
                for dimension in question.personality_dimensions:
                    if isinstance(dimension, PersonalityDimension) and dimension in scores:
                        scores[dimension] += 1.5
            
        except (ValueError, TypeError):
            raise InvalidAnswerException(
                f"Invalid answer format for question {question.id}"
            )
    
    async def determine_personality_types(
        self,
        scores: Dict[PersonalityDimension, float]
    ) -> Tuple[PersonalityType, PersonalityType]:
        """Определение основного и второстепенного типа личности"""
        # Сортируем по баллам
        sorted_scores = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        if len(sorted_scores) < 2:
            # Возвращаем дефолтные значения если недостаточно данных
            return PersonalityType.ROMANTIC, PersonalityType.ADVENTURER
        
        primary_dimension, primary_score = sorted_scores[0]
        secondary_dimension, secondary_score = sorted_scores[1]
        
        # Проверяем, что это действительно PersonalityDimension
        if not isinstance(primary_dimension, PersonalityDimension):
            logger.error(f"Primary dimension is not PersonalityDimension: {type(primary_dimension)}")
            return PersonalityType.ROMANTIC, PersonalityType.ADVENTURER
        
        if not isinstance(secondary_dimension, PersonalityDimension):
            logger.error(f"Secondary dimension is not PersonalityDimension: {type(secondary_dimension)}")
            return PersonalityType.ROMANTIC, PersonalityType.ADVENTURER
        
        # Преобразуем PersonalityDimension в PersonalityType
        try:
            primary = PersonalityType(primary_dimension.value)
            secondary = PersonalityType(secondary_dimension.value)
        except ValueError as e:
            logger.error(f"Error converting personality type: {e}. Using defaults.")
            return PersonalityType.ROMANTIC, PersonalityType.ADVENTURER
        
        return primary, secondary
    
    async def generate_interpretation(
        self,
        scores: Dict[PersonalityDimension, float],
        primary: PersonalityType,
        secondary: PersonalityType,
        template_personality_descriptions: Dict[str, str]
    ) -> str:
        """Генерация интерпретации результатов"""
        # Убеждаемся, что primary/secondary — это объекты PersonalityType
        try:
            if isinstance(primary, str):
                primary = PersonalityType(primary)
            if isinstance(secondary, str):
                secondary = PersonalityType(secondary)
        except ValueError as e:
            logger.error(f"Error converting personality types in generate_interpretation: {e}")
            primary = PersonalityType.ROMANTIC
            secondary = PersonalityType.ADVENTURER
        
        try:
            primary_str = primary.value
            secondary_str = secondary.value
        except Exception as e:
            logger.error(f"Error getting personality string values: {e}")
            primary_str = "romantic"
            secondary_str = "adventurer"
        
        try:
            primary_score = scores.get(PersonalityDimension(primary_str), 0)
            secondary_score = scores.get(PersonalityDimension(secondary_str), 0)
        except:
            primary_score = 0
            secondary_score = 0
        
        # Вычисляем общий процент
        total_score = sum(scores.values())
        max_possible_score = len(scores) * 3 * 10
        percentage = min(100, (total_score / max_possible_score) * 100) if max_possible_score > 0 else 0
        
        # Описание основного типа
        primary_desc = template_personality_descriptions.get(
            primary_str,
            "Этот тип личности отличается уникальными чертами характера."
        )
        
        # Описание комбинации типов
        combination_descriptions = {
            ("romantic", "caregiver"): "Вы сочетаете в себе эмоциональную глубину и заботу о других.",
            ("adventurer", "free_spirit"): "Ваша энергия и любовь к свободе делают вас интересным партнером.",
            ("intellectual", "leader"): "Вы обладаете аналитическим умом и лидерскими качествами.",
            ("caregiver", "leader"): "Вы умеете заботиться о других, при этом ведя их за собой.",
            ("romantic", "intellectual"): "Ваши отношения основаны на глубокой связи и интеллектуальной близости.",
            ("adventurer", "leader"): "Вы готовы вести за собой в новых приключениях.",
        }
        
        combination_key = (primary_str, secondary_str)
        if combination_key in combination_descriptions:
            combination_desc = combination_descriptions[combination_key]
        else:
            combination_desc = f"Комбинация {primary_str} и {secondary_str} создает уникальный характер."
        
        interpretation = f"""
        ## Результаты теста на определение типа личности
        
        ### Основной тип личности: {primary_str.title()}
        {primary_desc}
        
        ### Второстепенный тип: {secondary_str.title()}
        {combination_desc}
        
        ### Ваши сильные стороны:
        - Эмоциональный интеллект: {scores.get(PersonalityDimension.ROMANTIC, 0):.1f}/10
        - Дух приключений: {scores.get(PersonalityDimension.ADVENTURER, 0):.1f}/10
        - Интеллектуальные способности: {scores.get(PersonalityDimension.INTELLECTUAL, 0):.1f}/10
        - Заботливость: {scores.get(PersonalityDimension.CAREGIVER, 0):.1f}/10
        - Лидерские качества: {scores.get(PersonalityDimension.LEADER, 0):.1f}/10
        - Свободолюбие: {scores.get(PersonalityDimension.FREE_SPIRIT, 0):.1f}/10
        
        ### Общая оценка: {percentage:.1f}%
        """
        
        return interpretation
    
    async def generate_recommendations(
        self,
        primary: PersonalityType,
        secondary: PersonalityType,
        template_recommendations: Dict[str, List[str]]
    ) -> str:
        """Генерация рекомендаций на основе типа личности"""
        
        # Убеждаемся, что primary/secondary — это объекты PersonalityType
        try:
            if isinstance(primary, str):
                primary = PersonalityType(primary)
            if isinstance(secondary, str):
                secondary = PersonalityType(secondary)
        except ValueError as e:
            logger.error(f"Error converting personality types in generate_recommendations: {e}")
            primary = PersonalityType.ROMANTIC
            secondary = PersonalityType.ADVENTURER
        
        try:
            primary_str = primary.value
            secondary_str = secondary.value
        except Exception as e:
            logger.error(f"Error getting personality string values for recommendations: {e}")
            primary_str = "romantic"
            secondary_str = "adventurer"
        
        # Дефолтные рекомендации для каждого типа
        default_recommendations = {
            "romantic": [
                "Ищите партнера, который ценит глубокие разговоры",
                "Создавайте романтическую атмосферу в отношениях",
                "Выражайте свои чувства словами и жестами"
            ],
            "adventurer": [
                "Партнер должен разделять вашу любовь к приключениям",
                "Планируйте совместные путешествия и активности",
                "Будьте открыты новым впечатлениям вместе"
            ],
            "intellectual": [
                "Ищите умственного стимула в отношениях",
                "Участвуйте в совместном обучении и дискуссиях",
                "Посещайте культурные мероприятия вместе"
            ],
            "caregiver": [
                "Партнер должен ценить вашу заботу и внимание",
                "Создавайте уютную и поддерживающую атмосферу",
                "Проявляйте заботу через конкретные действия"
            ],
            "leader": [
                "Ищите партнера, который уважает ваши решения",
                "Ставьте совместные цели и достигайте их",
                "Берите инициативу в планировании будущего"
            ],
            "free_spirit": [
                "Партнер должен уважать вашу потребность в свободе",
                "Сохраняйте пространство для личного роста",
                "Ищите баланс между близостью и независимостью"
            ]
        }
        
        # Комбинируем рекомендации для двух типов
        primary_recs = template_recommendations.get(
            primary_str,
            default_recommendations.get(primary_str, [])
        )
        
        secondary_recs = template_recommendations.get(
            secondary_str,
            default_recommendations.get(secondary_str, [])
        )
        
        # Уникальные рекомендации для комбинации
        recommendations = list(set(primary_recs + secondary_recs))
        
        # Форматируем в строку
        recommendations_text = "### Рекомендации для поиска партнера:\n\n"
        for i, rec in enumerate(recommendations[:5], 1):
            recommendations_text += f"{i}. {rec}\n"
        
        return recommendations_text


# Глобальный экземпляр
_scoring_service = None

def get_scoring_service() -> ScoringService:
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service