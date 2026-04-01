FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sync.py .

# Cron: a cada 15 minutos
# Usando crond nativo do Alpine... mas estamos em slim debian, usar cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

COPY crontab.txt /etc/cron.d/pncp-sync
RUN chmod 0644 /etc/cron.d/pncp-sync && crontab /etc/cron.d/pncp-sync

CMD ["cron", "-f"]
