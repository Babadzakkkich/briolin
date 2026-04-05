FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/cache/transformers /app/cache/sentence-transformers

COPY shared/ /app/shared/

COPY ./profile-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./profile-service/app/ /app/app/

ENV TRANSFORMERS_CACHE=/app/cache/transformers
ENV SENTENCE_TRANSFORMERS_HOME=/app/cache/sentence-transformers

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]