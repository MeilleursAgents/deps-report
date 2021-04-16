FROM python:3.9-slim

COPY . /app
WORKDIR /app

RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create true && \
    poetry install --no-dev

CMD ["poetry", "run", "deps-report"]
