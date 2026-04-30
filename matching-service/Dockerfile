FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаём директории для кэша моделей
RUN mkdir -p /root/.cache/huggingface /root/.cache/sentence_transformers

COPY shared/ /app/shared/

COPY ./matching-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./matching-service/app/ /app/app/

# Устанавливаем переменные окружения для кэша моделей
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface
ENV HF_HOME=/root/.cache/huggingface
ENV SENTENCE_TRANSFORMERS_HOME=/root/.cache/sentence_transformers

# Предзагрузка модели (если ещё не в кэше)
# RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')" || true

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]