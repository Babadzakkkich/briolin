FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем shared директорию
COPY shared/ /app/shared/

# Копируем requirements и устанавливаем зависимости
COPY ./email-service/requirements.txt .

# Используем зеркало Huawei для стабильной загрузки
RUN pip install --no-cache-dir \
    --index-url https://mirrors.huaweicloud.com/repository/pypi/simple \
    --trusted-host mirrors.huaweicloud.com \
    --default-timeout=300 \
    --retries=10 \
    -r requirements.txt

# Копируем код email-service
COPY ./email-service/app/ /app/app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8008"]