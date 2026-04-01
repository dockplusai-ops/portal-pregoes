FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir requests psycopg2-binary

COPY sync.py .
COPY entrypoint.sh .

CMD ["/bin/bash", "/app/entrypoint.sh"]
