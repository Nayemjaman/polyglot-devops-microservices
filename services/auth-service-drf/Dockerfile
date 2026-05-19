FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

RUN POSTGRES_DB=build_db \
    POSTGRES_USER=build_user \
    POSTGRES_PASSWORD=build_password \
    POSTGRES_HOST=localhost \
    POSTGRES_PORT=5432 \
    python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "core.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "4"]
