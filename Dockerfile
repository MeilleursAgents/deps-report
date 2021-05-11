FROM python:3.9-slim

COPY . /app

RUN cd /app && \
    pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.in-project true && \
    poetry install --no-dev

CMD ["bash", "-c", "cd /app && poetry run deps-report"]
