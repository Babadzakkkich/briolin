FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY .shared/ /app/shared/

# Копируем requirements и устанавливаем зависимости
COPY ./testing-service/requirements.txt .
RUN pip install --no-cache-dir \
    --index-url http://mirrors.huaweicloud.com/repository/pypi/simple \
    --trusted-host mirrors.huaweicloud.com \
    --default-timeout=300 \
    --retries=10 \
    -r requirements.txt

# Копируем код auth-service
COPY ./testing-service/app/ /app/app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]