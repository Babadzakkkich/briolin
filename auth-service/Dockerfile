FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем shared директорию
COPY shared/ /app/shared/

# Копируем requirements и устанавливаем зависимости
COPY ./auth-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код auth-service
COPY ./auth-service/app/ /app/app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]