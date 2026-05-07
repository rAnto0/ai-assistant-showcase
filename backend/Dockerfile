FROM python:3.12-slim

WORKDIR /app

# Системные зависимости для sentence-transformers и pdfplumber
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# uv — копируем бинарник из официального образа
COPY --from=ghcr.io/astral-sh/uv:0.11.8 /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]