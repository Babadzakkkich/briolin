import random
from typing import List, Dict, Any
from bson import ObjectId

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import QuestionNotFoundException, MongoDBException
from app.database.session import mongo
from app.database.mongo_models import TestTemplate, Question


class TestGenerator:
    """Генератор тестов из пула вопросов"""
    
    async def get_active_test_template(self) -> TestTemplate:
        """Получение активного шаблона теста"""
        try:
            template_data = await mongo.test_templates.find_one(
                {"is_active": True},
                sort=[("updated_at", -1)]
            )
            
            if not template_data:
                template_data = await self._create_default_template()
            
            return TestTemplate(**template_data)
            
        except Exception as e:
            logger.error(f"Failed to get test template: {e}")
            raise MongoDBException("Failed to get test template")
    
    async def _create_default_template(self) -> Dict[str, Any]:
        """Создание дефолтного шаблона теста"""
        template = TestTemplate(
            id="dating_readiness_test_v1",
            name="Тест на готовность к знакомству",
            description="Пройдите тест, чтобы показать свою готовность к серьезным отношениям",
            question_count=settings.test_config.default_test_size,
            time_limit_minutes=settings.test_config.test_time_limit_minutes,
            pass_threshold=70.0,
            question_pool=[f"q{i}" for i in range(1, 16)]  # 15 вопросов
        )
        
        # Сохраняем в MongoDB
        result = await mongo.test_templates.insert_one(template.model_dump())
        
        # Создаем вопросы
        await self._create_default_questions()
        
        return template.model_dump()
    
    async def _create_default_questions(self):
        """Создание дефолтных вопросов для теста"""
        # Удаляем старые вопросы, чтобы избежать конфликтов
        await mongo.questions.delete_many({})
        
        questions = [
            {
                "id": "q1",
                "text": "Как вы обычно проводите свободное время?",
                "question_type": "multiple_choice",
                "difficulty": "easy",
                "category": "lifestyle",
                "tags": ["hobbies", "free_time"],
                "options": [
                    {"id": "a1", "text": "Активно: спорт, походы, встречи с друзьями", "score": 10, "is_correct": True},
                    {"id": "a2", "text": "Смешанно: иногда активно, иногда дома", "score": 8, "is_correct": True},
                    {"id": "a3", "text": "В основном дома: чтение, фильмы, хобби", "score": 6, "is_correct": False},
                    {"id": "a4", "text": "Предпочитаю одиночество", "score": 4, "is_correct": False}
                ]
            },
            {
                "id": "q2",
                "text": "Готовы ли вы к компромиссам в отношениях?",
                "question_type": "multiple_choice",
                "difficulty": "medium",
                "category": "relationships",
                "tags": ["compromise", "readiness"],
                "options": [
                    {"id": "a1", "text": "Да, это ключ к здоровым отношениям", "score": 10, "is_correct": True},
                    {"id": "a2", "text": "В большинстве случаев да", "score": 8, "is_correct": True},
                    {"id": "a3", "text": "Только в очень важных для меня вопросах", "score": 5, "is_correct": False},
                    {"id": "a4", "text": "Нет, я привык всегда быть правым", "score": 2, "is_correct": False}
                ]
            },
            {
                "id": "q3",
                "text": "Как часто вы общаетесь с новыми людьми?",
                "question_type": "likert_scale",
                "difficulty": "easy",
                "category": "social",
                "tags": ["social", "communication"],
                "min_value": 1,
                "max_value": 5,
                "labels": {"1": "Очень редко", "2": "Редко", "3": "Иногда", "4": "Часто", "5": "Постоянно"}
            },
            {
                "id": "q4",
                "text": "Что для вас главное в отношениях?",
                "question_type": "multiple_choice",
                "difficulty": "medium",
                "category": "values",
                "tags": ["relationships", "values"],
                "options": [
                    {"id": "a1", "text": "Доверие и честность", "score": 10, "is_correct": True},
                    {"id": "a2", "text": "Общие интересы", "score": 7, "is_correct": True},
                    {"id": "a3", "text": "Физическая привлекательность", "score": 5, "is_correct": False},
                    {"id": "a4", "text": "Материальная стабильность", "score": 3, "is_correct": False}
                ]
            },
            {
                "id": "q5",
                "text": "Как вы решаете конфликты?",
                "question_type": "multiple_choice",
                "difficulty": "medium",
                "category": "personality",
                "tags": ["conflict", "resolution"],
                "options": [
                    {"id": "a1", "text": "Обсуждаем спокойно и ищем решение", "score": 10, "is_correct": True},
                    {"id": "a2", "text": "Даю время остыть, потом говорим", "score": 9, "is_correct": True},
                    {"id": "a3", "text": "Избегаю конфронтации", "score": 4, "is_correct": False},
                    {"id": "a4", "text": "Могу повысить голос", "score": 2, "is_correct": False}
                ]
            },
            {
                "id": "q6",
                "text": "Сколько времени готовы уделять отношениям?",
                "question_type": "likert_scale",
                "difficulty": "easy",
                "category": "commitment",
                "tags": ["time", "commitment"],
                "min_value": 1,
                "max_value": 5,
                "labels": {"1": "Минимум", "2": "Мало", "3": "Умеренно", "4": "Много", "5": "Максимум"}
            },
            {
                "id": "q7",
                "text": "Как вы относитесь к онлайн-знакомствам?",
                "question_type": "multiple_choice",
                "difficulty": "easy",
                "category": "online_dating",
                "tags": ["online", "dating"],
                "options": [
                    {"id": "a1", "text": "Открыт к новым возможностям", "score": 10, "is_correct": True},
                    {"id": "a2", "text": "Позитивно, но осторожно", "score": 9, "is_correct": True},
                    {"id": "a3", "text": "Нейтрально", "score": 5, "is_correct": False},
                    {"id": "a4", "text": "Скептически", "score": 3, "is_correct": False}
                ]
            },
            {
                "id": "q8",
                "text": "Важна ли вам личная гигиена партнера?",
                "question_type": "true_false",
                "difficulty": "easy",
                "category": "values",
                "tags": ["hygiene", "standards"],
                "options": [
                    {"id": "a1", "text": "Да, очень важна", "score": 10, "is_correct": True},
                    {"id": "a2", "text": "Нет, не важна", "score": 0, "is_correct": False}
                ]
            },
            {
                "id": "q9",
                "text": "Готовы ли вы меняться ради партнера?",
                "question_type": "multiple_choice",
                "difficulty": "medium",
                "category": "personal_growth",
                "tags": ["change", "growth"],
                "options": [
                    {"id": "a1", "text": "Да, я всегда готов расти", "score": 10, "is_correct": True},
                    {"id": "a2", "text": "В разумных пределах", "score": 8, "is_correct": True},
                    {"id": "a3", "text": "Только если очень люблю", "score": 5, "is_correct": False},
                    {"id": "a4", "text": "Нет, я такой какой есть", "score": 2, "is_correct": False}
                ]
            },
            {
                "id": "q10",
                "text": "Как часто вы говорите партнеру комплименты?",
                "question_type": "likert_scale",
                "difficulty": "easy",
                "category": "communication",
                "tags": ["compliments", "communication"],
                "min_value": 1,
                "max_value": 5,
                "labels": {"1": "Никогда", "2": "Редко", "3": "Иногда", "4": "Часто", "5": "Постоянно"}
            },
            {
                "id": "q11",
                "text": "Что делаете, если партнер вам не отвечает?",
                "question_type": "multiple_choice",
                "difficulty": "medium",
                "category": "behavior",
                "tags": ["patience", "understanding"],
                "options": [
                    {"id": "a1", "text": "Жду спокойно, понимая что он может быть занят", "score": 10, "is_correct": True},
                    {"id": "a2", "text": "Пишу еще раз через некоторое время", "score": 7, "is_correct": True},
                    {"id": "a3", "text": "Начинаю волноваться и писать часто", "score": 3, "is_correct": False},
                    {"id": "a4", "text": "Обвиняю в игнорировании", "score": 0, "is_correct": False}
                ]
            },
            {
                "id": "q12",
                "text": "Можете ли вы прощать предательство?",
                "question_type": "multiple_choice",
                "difficulty": "hard",
                "category": "values",
                "tags": ["forgiveness", "boundaries"],
                "options": [
                    {"id": "a1", "text": "Да, если искренне раскаивается", "score": 6, "is_correct": False},
                    {"id": "a2", "text": "Зависит от обстоятельств", "score": 8, "is_correct": True},
                    {"id": "a3", "text": "Только один раз", "score": 5, "is_correct": False},
                    {"id": "a4", "text": "Никогда", "score": 7, "is_correct": True}
                ]
            },
            {
                "id": "q13",
                "text": "Важно ли вам мнение семьи о партнере?",
                "question_type": "multiple_choice",
                "difficulty": "medium",
                "category": "family",
                "tags": ["family", "opinions"],
                "options": [
                    {"id": "a1", "text": "Да, очень важно", "score": 8, "is_correct": True},
                    {"id": "a2", "text": "Уважаю, но решаю сам", "score": 10, "is_correct": True},
                    {"id": "a3", "text": "Немного важно", "score": 5, "is_correct": False},
                    {"id": "a4", "text": "Совсем не важно", "score": 3, "is_correct": False}
                ]
            },
            {
                "id": "q14",
                "text": "Каковы ваши планы на ближайшие 5 лет?",
                "question_type": "multiple_choice",
                "difficulty": "medium",
                "category": "future",
                "tags": ["future", "plans"],
                "options": [
                    {"id": "a1", "text": "Создать семью и быть счастливым", "score": 10, "is_correct": True},
                    {"id": "a2", "text": "Сосредоточиться на карьере", "score": 7, "is_correct": False},
                    {"id": "a3", "text": "Путешествовать и наслаждаться жизнью", "score": 6, "is_correct": False},
                    {"id": "a4", "text": "Еще не решил", "score": 4, "is_correct": False}
                ]
            },
            {
                "id": "q15",
                "text": "Готовы ли вы к компромиссам в быту?",
                "question_type": "multiple_choice",
                "difficulty": "easy",
                "category": "daily_life",
                "tags": ["compromise", "daily"],
                "options": [
                    {"id": "a1", "text": "Да, это нормально", "score": 10, "is_correct": True},
                    {"id": "a2", "text": "В большинстве вопросов", "score": 8, "is_correct": True},
                    {"id": "a3", "text": "Только в важных для меня", "score": 5, "is_correct": False},
                    {"id": "a4", "text": "Нет, я сам по себе", "score": 2, "is_correct": False}
                ]
            }
        ]
        
        # Сохраняем вопросы в MongoDB
        await mongo.questions.insert_many(questions)
        logger.info(f"Created {len(questions)} default questions in MongoDB")
    
    async def get_questions_by_ids(self, question_ids: List[str]) -> List[Question]:
        """Получение вопросов по списку ID"""
        try:
            cursor = mongo.questions.find({"id": {"$in": question_ids}})
            questions_data = await cursor.to_list(length=len(question_ids))
            
            if len(questions_data) != len(question_ids):
                missing = set(question_ids) - {q["id"] for q in questions_data}
                raise QuestionNotFoundException(f"Questions not found: {missing}")
            
            return [Question(**q) for q in questions_data]
            
        except QuestionNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get questions: {e}")
            raise MongoDBException("Failed to get questions")
    
    async def generate_test_questions(self, template: TestTemplate) -> List[Question]:
        """Генерация случайного набора вопросов для теста"""
        try:
            if len(template.question_pool) <= template.question_count:
                selected_ids = template.question_pool
            else:
                selected_ids = random.sample(
                    template.question_pool,
                    template.question_count
                )
            
            questions = await self.get_questions_by_ids(selected_ids)
            
            for question in questions:
                if question.question_type == "likert_scale":
                    if question.min_value is None:
                        question.min_value = 1
                    if question.max_value is None:
                        question.max_value = 5
            
            random.shuffle(questions)
            
            return questions
            
        except Exception as e:
            logger.error(f"Failed to generate test questions: {e}")
            raise
    
    async def get_question_by_id(self, question_id: str) -> Question:
        """Получение вопроса по ID"""
        try:
            question_data = await mongo.questions.find_one({"id": question_id})
            if not question_data:
                raise QuestionNotFoundException(f"Question {question_id} not found")
            
            return Question(**question_data)
            
        except QuestionNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get question: {e}")
            raise MongoDBException("Failed to get question")


_test_generator = None

def get_test_generator() -> TestGenerator:
    global _test_generator
    if _test_generator is None:
        _test_generator = TestGenerator()
    return _test_generator