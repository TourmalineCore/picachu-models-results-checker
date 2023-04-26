FROM python:3.10.9-slim as base

ENV PATH /opt/venv/bin:$PATH
ENV PYTHONFAULTHANDLER 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

FROM base AS builder

WORKDIR /opt

RUN python -m venv venv
RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

FROM base as runtime
WORKDIR /opt
COPY --from=builder /opt/venv venv

COPY . .
CMD poetry run python application.py