FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY static ./static
COPY templates ./templates
COPY migrations ./migrations
COPY util ./util
COPY config.py alembic.ini init_db.py wsgi.py ./

EXPOSE 8080

CMD ["sh", "-c", "flask --app wsgi run --host 0.0.0.0 --port ${PORT}"]
