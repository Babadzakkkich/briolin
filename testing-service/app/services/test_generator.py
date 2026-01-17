import random
from typing import List, Dict, Any
from bson import ObjectId

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import QuestionNotFoundException, MongoDBException
from app.database.session import mongo
from app.database.mongo_models import TestTemplate, Question, PersonalityDimension


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
                # Создаем тестовый шаблон, если нет активного
                template_data = await self._create_default_template()
            
            return TestTemplate(**template_data)
            
        except Exception as e:
            logger.error(f"Failed to get test template: {e}")
            raise MongoDBException("Failed to get test template")
    
    async def _create_default_template(self) -> Dict[str, Any]:
        """Создание дефолтного шаблона теста"""
        template = TestTemplate(
            id="default_personality_test",
            name="Тест на определение типа личности",
            description="Определите ваш тип личности для лучшего подбора партнера",
            question_count=settings.test_config.default_test_size,
            time_limit_minutes=settings.test_config.test_time_limit_minutes,
            question_pool=[f"q{i}" for i in range(1, settings.test_config.question_pool_size + 1)],
            personality_descriptions={
                PersonalityDimension.ROMANTIC: "Романтики ценят глубокие эмоциональные связи, жесты внимания и создание особенной атмосферы в отношениях.",
                PersonalityDimension.ADVENTURER: "Искатели приключений любят новизну, спонтанность и активный отдых. Они заряжают энергией и оптимизмом.",
                PersonalityDimension.INTELLECTUAL: "Интеллектуалы стремятся к ментальной стимуляции, глубоким разговорам и совместному познанию мира.",
                PersonalityDimension.CAREGIVER: "Заботливые натуры находят счастье в помощи другим, создании уюта и эмоциональной поддержке.",
                PersonalityDimension.LEADER: "Лидеры ценят целеустремленность, ответственность и способность вдохновлять других на достижения.",
                PersonalityDimension.FREE_SPIRIT: "Свободные души стремятся к независимости, творческому самовыражению и жизни без ограничений.",
            }
        )
        
        # Сохраняем в MongoDB
        result = await mongo.test_templates.insert_one(template.model_dump())
        
        # Создаем вопросы, если их нет
        await self._create_default_questions()
        
        return template.model_dump()
    
    async def _create_default_questions(self):
        """Создание дефолтных вопросов для теста"""
        questions = [
            Question(
                id="q1",
                text="Как вы обычно проводите выходные?",
                question_type="multiple_choice",
                category="lifestyle",
                tags=["weekend", "hobbies"],
                personality_dimensions=["intellectual", "romantic", "adventurer", "caregiver", "leader"],  # ДОБАВЬТЕ
                options=[
                    {
                        "id": "a1",
                        "text": "Читаю книги или смотрю фильмы дома",
                        "score_impact": {"intellectual": 2, "romantic": 1}
                    },
                    {
                        "id": "a2",
                        "text": "Отправляюсь в поход или путешествие",
                        "score_impact": {"adventurer": 3, "free_spirit": 2}
                    },
                    {
                        "id": "a3",
                        "text": "Встречаюсь с друзьями или помогаю родным",
                        "score_impact": {"caregiver": 2, "leader": 1}
                    },
                    {
                        "id": "a4",
                        "text": "Работаю над личными проектами или изучаю что-то новое",
                        "score_impact": {"intellectual": 3, "leader": 1}
                    }
                ]
            ),
            Question(
                id="q2",
                text="Что для вас важнее в отношениях?",
                question_type="multiple_choice",
                category="relationships",
                tags=["values", "priorities"],
                personality_dimensions=["romantic", "adventurer", "intellectual", "caregiver"],  # ДОБАВЬТЕ
                options=[
                    {
                        "id": "a1",
                        "text": "Глубокое эмоциональное соединение и понимание",
                        "score_impact": {"romantic": 3, "caregiver": 2}
                    },
                    {
                        "id": "a2",
                        "text": "Совместные приключения и новые впечатления",
                        "score_impact": {"adventurer": 3, "free_spirit": 2}
                    },
                    {
                        "id": "a3",
                        "text": "Интеллектуальная совместимость и общие интересы",
                        "score_impact": {"intellectual": 3, "leader": 1}
                    },
                    {
                        "id": "a4",
                        "text": "Поддержка и взаимопомощь в достижении целей",
                        "score_impact": {"caregiver": 2, "leader": 2}
                    }
                ]
            ),
            Question(
                id="q3",
                text="Как вы принимаете важные решения?",
                question_type="likert_scale",
                category="personality",
                tags=["decision_making"],
                min_value=1,
                max_value=5,
                labels={
                    "1": "Полагаюсь на интуицию и чувства",
                    "2": "Скорее на интуицию",
                    "3": "Баланс разума и чувств",
                    "4": "Скорее на анализ",
                    "5": "Тщательно анализирую все факты"
                },
                personality_dimensions=["intellectual", "free_spirit"]
            ),
            Question(
                id="q4",
                text="Что вы цените в друзьях больше всего?",
                question_type="multiple_choice",
                category="social",
                tags=["friendship", "values"],
                personality_dimensions=["caregiver", "intellectual", "adventurer", "leader"],  # ДОБАВЬТЕ
                options=[
                    {
                        "id": "a1",
                        "text": "Верность и поддержку в трудную минуту",
                        "score_impact": {"caregiver": 3, "romantic": 1}
                    },
                    {
                        "id": "a2",
                        "text": "Способность вдохновлять на новые идеи",
                        "score_impact": {"intellectual": 2, "leader": 2}
                    },
                    {
                        "id": "a3",
                        "text": "Готовность к спонтанным приключениям",
                        "score_impact": {"adventurer": 3, "free_spirit": 2}
                    },
                    {
                        "id": "a4",
                        "text": "Честность и прямое выражение мыслей",
                        "score_impact": {"leader": 2, "intellectual": 2}
                    }
                ]
            ),
            Question(
                id="q5",
                text="Ваше отношение к планированию?",
                question_type="likert_scale",
                category="personality",
                tags=["planning", "organization"],
                min_value=1,
                max_value=5,
                labels={
                    "1": "Предпочитаю спонтанность",
                    "2": "Скорее спонтанный",
                    "3": "Умеренное планирование",
                    "4": "Люблю планировать",
                    "5": "Детально планирую всё заранее"
                },
                personality_dimensions=["free_spirit", "leader"]
            ),
            Question(
                id="q6",
                text="Что для вас идеальный отпуск?",
                question_type="multiple_choice",
                category="lifestyle",
                tags=["vacation", "travel"],
                personality_dimensions=["romantic", "adventurer", "intellectual", "caregiver"],  # ДОБАВЬТЕ
                options=[
                    {
                        "id": "a1",
                        "text": "Романтическое путешествие в красивое место",
                        "score_impact": {"romantic": 3, "adventurer": 1}
                    },
                    {
                        "id": "a2",
                        "text": "Экстремальное приключение в дикой природе",
                        "score_impact": {"adventurer": 3, "free_spirit": 2}
                    },
                    {
                        "id": "a3",
                        "text": "Познавательный тур с изучением культуры",
                        "score_impact": {"intellectual": 3, "leader": 1}
                    },
                    {
                        "id": "a4",
                        "text": "Спокойный отдых с близкими людьми",
                        "score_impact": {"caregiver": 3, "romantic": 1}
                    }
                ]
            ),
            Question(
                id="q7",
                text="Как вы относитесь к рутине?",
                question_type="likert_scale",
                category="personality",
                tags=["routine", "stability"],
                min_value=1,
                max_value=5,
                labels={
                    "1": "Ненавижу, стараюсь избегать",
                    "2": "Не люблю, но терплю",
                    "3": "Нейтрально",
                    "4": "Принимаю как необходимость",
                    "5": "Нахожу в ней комфорт и стабильность"
                },
                personality_dimensions=["free_spirit", "caregiver"]
            ),
            Question(
                id="q8",
                text="Что мотивирует вас больше всего?",
                question_type="multiple_choice",
                category="motivation",
                tags=["goals", "inspiration"],
                personality_dimensions=["caregiver", "adventurer", "intellectual", "free_spirit"],  # ДОБАВЬТЕ
                options=[
                    {
                        "id": "a1",
                        "text": "Возможность помогать другим",
                        "score_impact": {"caregiver": 3, "romantic": 1}
                    },
                    {
                        "id": "a2",
                        "text": "Новые вызовы и достижения",
                        "score_impact": {"adventurer": 2, "leader": 2}
                    },
                    {
                        "id": "a3",
                        "text": "Стремление к знаниям и пониманию",
                        "score_impact": {"intellectual": 3, "leader": 1}
                    },
                    {
                        "id": "a4",
                        "text": "Свобода самовыражения",
                        "score_impact": {"free_spirit": 3, "adventurer": 1}
                    }
                ]
            ),
            Question(
                id="q9",
                text="Как вы выражаете любовь и заботу?",
                question_type="multiple_choice",
                category="relationships",
                tags=["love_language", "care"],
                personality_dimensions=["romantic", "caregiver", "leader", "free_spirit"],  # ДОБАВЬТЕ
                options=[
                    {
                        "id": "a1",
                        "text": "Через слова поддержки и комплименты",
                        "score_impact": {"romantic": 3, "caregiver": 2}
                    },
                    {
                        "id": "a2",
                        "text": "Помогая в решении проблем",
                        "score_impact": {"caregiver": 3, "leader": 1}
                    },
                    {
                        "id": "a3",
                        "text": "Организуя интересные мероприятия",
                        "score_impact": {"leader": 2, "adventurer": 2}
                    },
                    {
                        "id": "a4",
                        "text": "Давая свободу и пространство",
                        "score_impact": {"free_spirit": 3, "intellectual": 1}
                    }
                ]
            ),
            Question(
                id="q10",
                text="Ваше отношение к правилам?",
                question_type="likert_scale",
                category="personality",
                tags=["rules", "conformity"],
                min_value=1,
                max_value=5,
                labels={
                    "1": "Часто их нарушаю",
                    "2": "Иногда игнорирую",
                    "3": "Следую, если они разумны",
                    "4": "Стараюсь соблюдать",
                    "5": "Строго следую правилам"
                },
                personality_dimensions=["free_spirit", "leader"]
            ),
            Question(
                id="q11",
                text="Что для вас важнее в работе?",
                question_type="multiple_choice",
                category="career",
                tags=["work", "values"],
                personality_dimensions=["free_spirit", "caregiver", "leader", "intellectual"],  # ДОБАВЬТЕ
                options=[
                    {
                        "id": "a1",
                        "text": "Творческая свобода",
                        "score_impact": {"free_spirit": 3, "intellectual": 1}
                    },
                    {
                        "id": "a2",
                        "text": "Стабильность и надежность",
                        "score_impact": {"caregiver": 2, "leader": 1}
                    },
                    {
                        "id": "a3",
                        "text": "Возможность влиять и руководить",
                        "score_impact": {"leader": 3, "adventurer": 1}
                    },
                    {
                        "id": "a4",
                        "text": "Постоянное обучение и развитие",
                        "score_impact": {"intellectual": 3, "adventurer": 1}
                    }
                ]
            ),
            Question(
                id="q12",
                text="Как вы справляетесь со стрессом?",
                question_type="multiple_choice",
                category="personality",
                tags=["stress", "coping"],
                personality_dimensions=["caregiver", "intellectual", "adventurer", "leader"],  # ДОБАВЬТЕ
                options=[
                    {
                        "id": "a1",
                        "text": "Ищу поддержку у близких",
                        "score_impact": {"caregiver": 2, "romantic": 2}
                    },
                    {
                        "id": "a2",
                        "text": "Анализирую ситуацию и ищу решение",
                        "score_impact": {"intellectual": 3, "leader": 1}
                    },
                    {
                        "id": "a3",
                        "text": "Меняю обстановку или отправляюсь в путешествие",
                        "score_impact": {"adventurer": 3, "free_spirit": 2}
                    },
                    {
                        "id": "a4",
                        "text": "Беру всё под контроль и действую",
                        "score_impact": {"leader": 3, "adventurer": 1}
                    }
                ]
            ),
            Question(
                id="q13",
                text="Ваше отношение к искусству?",
                question_type="likert_scale",
                category="interests",
                tags=["art", "culture"],
                min_value=1,
                max_value=5,
                labels={
                    "1": "Не интересуюсь",
                    "2": "Иногда обращаю внимание",
                    "3": "Нравится, но не глубоко",
                    "4": "Люблю и ценю",
                    "5": "Живу искусством"
                },
                personality_dimensions=["romantic", "intellectual"]
            ),
            Question(
                id="q14",
                text="Что для вас значит успех?",
                question_type="multiple_choice",
                category="values",
                tags=["success", "achievement"],
                personality_dimensions=["romantic", "free_spirit", "leader", "caregiver"],  # ДОБАВЬТЕ
                options=[
                    {
                        "id": "a1",
                        "text": "Гармоничные отношения и семья",
                        "score_impact": {"romantic": 3, "caregiver": 2}
                    },
                    {
                        "id": "a2",
                        "text": "Личная свобода и самореализация",
                        "score_impact": {"free_spirit": 3, "adventurer": 1}
                    },
                    {
                        "id": "a3",
                        "text": "Достижение целей и признание",
                        "score_impact": {"leader": 3, "intellectual": 1}
                    },
                    {
                        "id": "a4",
                        "text": "Вклад в развитие общества",
                        "score_impact": {"caregiver": 3, "intellectual": 1}
                    }
                ]
            ),
            Question(
                id="q15",
                text="Как вы относитесь к изменениям?",
                question_type="likert_scale",
                category="personality",
                tags=["change", "adaptability"],
                min_value=1,
                max_value=5,
                labels={
                    "1": "Избегаю любой ценой",
                    "2": "Не люблю, но адаптируюсь",
                    "3": "Нейтрально",
                    "4": "Приветствую",
                    "5": "Сам создаю изменения"
                },
                personality_dimensions=["free_spirit", "adventurer"]
            )
        ]
        
        # Сохраняем вопросы в MongoDB
        for question in questions:
            # Убедимся, что personality_dimensions не None
            if not question.personality_dimensions:
                question.personality_dimensions = ["romantic", "adventurer"]  # default
            
            await mongo.questions.update_one(
                {"id": question.id},
                {"$set": question.model_dump()},
                upsert=True
            )
    
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
            # Берем случайные вопросы из пула
            if len(template.question_pool) <= template.question_count:
                selected_ids = template.question_pool
            else:
                selected_ids = random.sample(
                    template.question_pool, 
                    template.question_count
                )
            
            # Получаем полные объекты вопросов
            questions = await self.get_questions_by_ids(selected_ids)
            
            # Проверяем, что у всех вопросов корректные данные
            for question in questions:
                if question.question_type == "likert_scale":
                    if question.min_value is None:
                        question.min_value = 1
                    if question.max_value is None:
                        question.max_value = 5
                if question.personality_dimensions is None:
                    question.personality_dimensions = []
            
            # Перемешиваем порядок вопросов
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


# Глобальный экземпляр
_test_generator = None

def get_test_generator() -> TestGenerator:
    global _test_generator
    if _test_generator is None:
        _test_generator = TestGenerator()
    return _test_generator