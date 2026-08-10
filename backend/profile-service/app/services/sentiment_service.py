import asyncio
from typing import Optional, List, Dict
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

from app.core.logger import logger


class SentimentService:
    """
    Сервис для анализа тональности текста.
    Использует yangheng/deberta-v3-base-absa-v1.1 как классификатор.
    
    Модель multilingual (включая русский), DeBERTa-v3 архитектура.
    """
    
    MODEL_NAME = "yangheng/deberta-v3-base-absa-v1.1"
    
    def __init__(self):
        self._model: Optional[AutoModelForSequenceClassification] = None
        self._tokenizer: Optional[AutoTokenizer] = None
        self._lock = asyncio.Lock()
        # Лейблы по умолчанию (переопределяются из конфига модели)
        self.id2label = {0: "NEGATIVE", 1: "NEUTRAL", 2: "POSITIVE"}
    
    async def _get_model(self):
        """Ленивая инициализация модели классификации"""
        if self._model is None:
            async with self._lock:
                if self._model is None:
                    logger.info(f"Loading sentiment classification model: {self.MODEL_NAME}")
                    
                    try:
                        loop = asyncio.get_event_loop()
                        
                        # Загружаем токенизатор и модель
                        self._tokenizer = await loop.run_in_executor(
                            None,
                            lambda: AutoTokenizer.from_pretrained(self.MODEL_NAME)
                        )
                        self._model = await loop.run_in_executor(
                            None,
                            lambda: AutoModelForSequenceClassification.from_pretrained(self.MODEL_NAME)
                        )
                        
                        self._model.eval()
                        
                        # Определяем лейблы из конфига модели
                        if hasattr(self._model.config, 'id2label'):
                            self.id2label = self._model.config.id2label
                        
                        logger.info(f"Model labels: {self.id2label}")
                        logger.info(f"Sentiment classification model loaded successfully")
                    except Exception as e:
                        logger.error(f"Failed to load sentiment model: {e}")
                        raise
        
        return self._model, self._tokenizer
    
    def _build_sentiment_vector(self, probs: np.ndarray) -> Dict:
        """
        Строит sentiment_vector из массива вероятностей [class0, class1, class2].
        Маппинг классов берется из id2label.
        """
        pos_score = neg_score = neu_score = 0.0
        
        for idx, label in self.id2label.items():
            score = float(probs[idx])
            if label.upper() in ("POSITIVE", "POS"):
                pos_score = score
            elif label.upper() in ("NEGATIVE", "NEG"):
                neg_score = score
            elif label.upper() in ("NEUTRAL", "NEU"):
                neu_score = score
        
        # Определяем доминирующую метку
        max_score = max(pos_score, neg_score, neu_score)
        if max_score == pos_score:
            dominant_label = "POSITIVE"
        elif max_score == neg_score:
            dominant_label = "NEGATIVE"
        else:
            dominant_label = "NEUTRAL"
        
        return {
            "label": dominant_label,
            "scores": {
                "POSITIVE": pos_score,
                "NEGATIVE": neg_score,
                "NEUTRAL": neu_score
            },
            "sentiment_vector": [pos_score, neg_score, neu_score]
        }
    
    async def analyze_sentiment(self, text: str) -> Dict:
        """
        Анализирует тональность текста.
        
        Returns:
            dict с:
            - label: "POSITIVE", "NEGATIVE", или "NEUTRAL"
            - scores: {POSITIVE, NEGATIVE, NEUTRAL}
            - sentiment_vector: [pos, neg, neu]
        """
        if not text or not text.strip():
            return {
                "label": "NEUTRAL",
                "scores": {"POSITIVE": 0.0, "NEGATIVE": 0.0, "NEUTRAL": 1.0},
                "sentiment_vector": [0.0, 0.0, 1.0]
            }
        
        try:
            model, tokenizer = await self._get_model()
            
            loop = asyncio.get_event_loop()
            
            def _analyze():
                inputs = tokenizer(
                    text,
                    max_length=512,
                    padding=True,
                    truncation=True,
                    return_tensors="pt"
                )
                
                with torch.no_grad():
                    outputs = model(**inputs)
                
                # Получаем вероятности через softmax
                logits = outputs.logits.squeeze()
                probs = F.softmax(logits, dim=-1).cpu().numpy()
                
                return self._build_sentiment_vector(probs)
            
            result = await loop.run_in_executor(None, _analyze)
            
            logger.debug(
                f"Sentiment analysis: '{text[:50]}...' → {result['label']} "
                f"(POS={result['scores']['POSITIVE']:.3f}, "
                f"NEG={result['scores']['NEGATIVE']:.3f}, "
                f"NEU={result['scores']['NEUTRAL']:.3f})"
            )
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {e}", exc_info=True)
            return {
                "label": "NEUTRAL",
                "scores": {"POSITIVE": 0.0, "NEGATIVE": 0.0, "NEUTRAL": 1.0},
                "sentiment_vector": [0.0, 0.0, 1.0]
            }
    
    async def generate_sentiment_embedding(self, text: str) -> Optional[List[float]]:
        """Генерирует тональный вектор (POS, NEG, NEU)."""
        result = await self.analyze_sentiment(text)
        return result["sentiment_vector"]
    
    async def get_sentiment_vector(self, text: str) -> Optional[List[float]]:
        """Алиас для generate_sentiment_embedding"""
        return await self.generate_sentiment_embedding(text)


_sentiment_service: Optional[SentimentService] = None

def get_sentiment_service() -> SentimentService:
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = SentimentService()
    return _sentiment_service