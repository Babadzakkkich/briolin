import asyncio
from datetime import datetime
from database.session import mongo
from core.logger import logger

async def migrate_questions():
    """Миграция вопросов из score_impact в score"""
    logger.info("Starting questions migration...")
    
    # Находим все вопросы
    questions = await mongo.questions.find({}).to_list(length=None)
    
    migrated = 0
    errors = 0
    
    for question in questions:
        try:
            question_id = question["id"]
            options = question.get("options", [])
            
            new_options = []
            for option in options:
                # Удаляем старые поля
                option.pop("score_impact", None)
                
                # Добавляем новое поле score
                if "score" not in option:
                    # Дефолтные значения на основе is_correct или 5 баллов
                    if option.get("is_correct"):
                        option["score"] = 10.0
                    else:
                        option["score"] = 5.0
                
                new_options.append(option)
            
            # Обновляем вопрос
            await mongo.questions.update_one(
                {"id": question_id},
                {
                    "$set": {
                        "options": new_options,
                        "updated_at": datetime.utcnow()
                    },
                    "$unset": {
                        "personality_dimensions": 1,  # Удаляем старое поле
                        "score_impact": 1
                    }
                }
            )
            
            migrated += 1
            
        except Exception as e:
            logger.error(f"Error migrating question {question.get('id')}: {e}")
            errors += 1
    
    logger.info(f"Migration complete: {migrated} migrated, {errors} errors")

if __name__ == "__main__":
    asyncio.run(migrate_questions())