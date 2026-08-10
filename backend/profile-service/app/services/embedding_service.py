import asyncio
import os
from pathlib import Path
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from app.core.logger import logger


class EmbeddingService:
    """Сервис для генерации эмбеддингов с использованием sentence-transformers"""
    
    MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
    
    def __init__(self):
        self._model: Optional[SentenceTransformer] = None
        self._lock = asyncio.Lock()
        self._cache_dir = self._get_cache_dir()
    
    def _get_cache_dir(self) -> str:
        """Определяет директорию для кэша модели"""
        # Проверяем переменные окружения
        cache_dir = os.environ.get("SENTENCE_TRANSFORMERS_HOME")
        if cache_dir:
            return cache_dir
        
        # Или стандартная директория
        home = Path.home()
        cache_dir = home / ".cache" / "sentence_transformers"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return str(cache_dir)
    
    async def _get_model(self) -> SentenceTransformer:
        """Ленивая инициализация модели с проверкой кэша"""
        if self._model is None:
            async with self._lock:
                if self._model is None:
                    logger.info(f"Loading embedding model: {self.MODEL_NAME}")
                    logger.info(f"Cache directory: {self._cache_dir}")
                    
                    # Проверяем, есть ли модель в кэше
                    model_path = Path(self._cache_dir) / self.MODEL_NAME.replace("/", "_")
                    if model_path.exists():
                        logger.info(f"Model found in cache: {model_path}")
                    else:
                        logger.info("Model not in cache, will download...")
                    
                    try:
                        loop = asyncio.get_event_loop()
                        self._model = await loop.run_in_executor(
                            None,
                            lambda: SentenceTransformer(
                                self.MODEL_NAME,
                                cache_folder=self._cache_dir
                            )
                        )
                        logger.info("Embedding model loaded successfully")
                        logger.info(f"Model saved to: {self._cache_dir}")
                    except Exception as e:
                        logger.error(f"Failed to load embedding model: {e}")
                        raise
        return self._model
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Генерация эмбеддинга из текста"""
        if not text or not text.strip():
            logger.warning("Empty text for embedding generation")
            return None
        
        try:
            model = await self._get_model()
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: model.encode(text, normalize_embeddings=True)
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}", exc_info=True)
            return None
    
    async def generate_profile_embedding(
        self,
        about_me: Optional[str] = None,
        hobbies: Optional[str] = None,
        partner_preferences: Optional[str] = None
    ) -> Optional[List[float]]:
        """Генерация эмбеддинга из полей профиля"""
        text_parts = []
        if about_me:
            text_parts.append(about_me)
        if hobbies:
            text_parts.append(hobbies)
        if partner_preferences:
            text_parts.append(partner_preferences)
        
        combined_text = " ".join(text_parts)
        
        if not combined_text:
            logger.warning("No text for embedding generation")
            return None
        
        logger.debug(f"Generating embedding for text length: {len(combined_text)}")
        return await self.generate_embedding(combined_text)


# Глобальный экземпляр
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service