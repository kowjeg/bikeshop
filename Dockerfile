FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

ARG DEV=false

RUN poetry config virtualenvs.create false \
    && if [ "$DEV" = "true" ]; \
       then poetry install --with dev --no-root; \
       else poetry install --only main --no-root; fi

COPY . .

EXPOSE 8000