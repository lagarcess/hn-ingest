FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY hn_ingest hn_ingest
RUN mkdir -p /app/data

ENV DATABASE_PATH=/app/data/hn.db \
    PORT=8000 \
    LOG_LEVEL=info \
    HN_BASE_URL=https://hacker-news.firebaseio.com/v0

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn hn_ingest.app:app --host 0.0.0.0 --port ${PORT} --log-level ${LOG_LEVEL}"]
