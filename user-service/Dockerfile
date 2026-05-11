FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Установка системных зависимостей включая Rust
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    build-essential \
    libc6-dev \
    pkg-config \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && rm -rf /var/lib/apt/lists/*

# Добавляем Rust в PATH
ENV PATH="/root/.cargo/bin:${PATH}"

COPY shared/ /app/shared/

COPY ./user-service/requirements.txt .

# Используем зеркало для стабильной загрузки
RUN pip install --no-cache-dir \
    --index-url http://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    --default-timeout=300 \
    --retries=10 \
    -r requirements.txt

COPY ./user-service/app/ /app/app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]